/* ============================================================
   player.js — Termux Media Server (Phase 5 + subtitles)

   Subtitles:
     - initSubtitleSelector() adds HTML5 <track> elements to the
       video element for each subtitle stream the server extracted.
     - The browser renders the WebVTT overlay natively — no custom
       rendering needed.
     - "Off" is the default state; user explicitly opts in.
     - Switching tracks works via the TextTrack API (mode: showing /
       disabled), which is independent of hls.js.
   ============================================================ */

(function () {
  "use strict";

  /* ----------------------------------------------------------
     DOM references
  ---------------------------------------------------------- */
  var videoEl       = document.getElementById("video-player");
  var overlayEl     = document.getElementById("loading-overlay");
  var spinnerEl     = document.getElementById("spinner");
  var overlayText   = document.getElementById("overlay-text");
  var statusDot     = document.getElementById("status-dot");
  var statusText    = document.getElementById("status-text");
  var audioSelector = document.getElementById("audio-selector");
  var audioSelect   = document.getElementById("audio-track");
  var subSelector   = document.getElementById("sub-selector");
  var subSelect     = document.getElementById("sub-track");

  /* ----------------------------------------------------------
     Config
  ---------------------------------------------------------- */
  var VIDEO_ID      = videoEl.dataset.videoId;
  var POLL_INTERVAL = 1500;
  var MAX_NET_ERRS  = 6;

  /* ----------------------------------------------------------
     State
  ---------------------------------------------------------- */
  var pollTimer     = null;
  var hlsInstance   = null;
  var netErrCount   = 0;
  var myTextTracks  = [];   // TextTrack objects for our subtitle tracks

  /* ==========================================================
     UI helpers
  ========================================================== */

  function showOverlay(msg, isError) {
    overlayEl.classList.remove("hidden");
    overlayText.textContent = msg;
    if (isError) {
      overlayText.classList.add("error");
      spinnerEl.style.display = "none";
    } else {
      overlayText.classList.remove("error");
      spinnerEl.style.display = "";
    }
  }

  function hideOverlay() {
    overlayEl.classList.add("hidden");
  }

  function setStatus(msg, dotClass) {
    statusText.textContent = msg;
    statusDot.className    = "status-dot";
    if (dotClass) statusDot.classList.add(dotClass);
  }

  /* ==========================================================
     POLLING
  ========================================================== */

  function startPolling() {
    showOverlay("Preparing stream\u2026");
    setStatus("Connecting\u2026", "loading");
    poll();
    pollTimer = setInterval(poll, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer !== null) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function poll() {
    fetch("/api/status/" + VIDEO_ID)
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        netErrCount = 0;
        handleStatus(data);
      })
      .catch(function (err) {
        netErrCount++;
        console.warn("[Player] Poll error (" + netErrCount + "):", err.message);

        if (netErrCount >= MAX_NET_ERRS) {
          stopPolling();
          showOverlay(
            "Cannot reach the media server.\nIs it still running? (Check the Termux terminal.)",
            true
          );
          setStatus("Connection lost", "error");
        } else {
          setStatus(
            "Retrying\u2026 (" + netErrCount + "/" + MAX_NET_ERRS + ")",
            "loading"
          );
        }
      });
  }

  function handleStatus(data) {
    switch (data.status) {

      case "pending":
        showOverlay("Waiting for a transcoding slot\u2026");
        setStatus("Queued", "loading");
        break;

      case "transcoding":
        showOverlay(data.message || "Transcoding video \u2014 please wait\u2026");
        setStatus("Transcoding", "loading");
        break;

      case "ready":
        stopPolling();
        hideOverlay();
        setStatus("Ready", "active");
        initAudioSelector(data.audio_tracks || []);
        initSubtitleSelector(data.subtitle_tracks || []);
        initHLS(data.hls_url);
        break;

      case "failed": {
        stopPolling();
        var msg = data.error
          ? "Error: " + data.error
          : "Transcoding failed. Check the Termux terminal for details.";
        showOverlay(msg, true);
        setStatus("Failed", "error");
        console.error("[Player] Transcode failed:", data);
        break;
      }

      case "unknown":
        stopPolling();
        showOverlay("Job not found. Try reloading the page.", true);
        setStatus("Unknown", "error");
        break;

      default:
        console.warn("[Player] Unexpected status:", data.status);
        setStatus("Status: " + data.status, "loading");
    }
  }

  /* ==========================================================
     AUDIO SELECTOR
  ========================================================== */

  function initAudioSelector(tracks) {
    if (!tracks || tracks.length <= 1) {
      audioSelector.style.display = "none";
      return;
    }

    audioSelect.innerHTML = "";
    tracks.forEach(function (track, i) {
      var opt         = document.createElement("option");
      opt.value       = i;
      opt.textContent = track.name;
      audioSelect.appendChild(opt);
    });

    audioSelector.style.display = "";

    audioSelect.addEventListener("change", function () {
      if (!hlsInstance) return;
      var idx = parseInt(this.value, 10);
      if (!isNaN(idx)) hlsInstance.audioTrack = idx;
    });
  }

  /* ==========================================================
     SUBTITLE SELECTOR
  ========================================================== */

  function initSubtitleSelector(tracks) {
    if (!tracks || tracks.length === 0) {
      subSelector.style.display = "none";
      return;
    }

    /*
     * Add one <track kind="subtitles"> element per track.
     * We keep references to the underlying TextTrack objects in
     * myTextTracks[] so we can toggle them without scanning
     * videoEl.textTracks (which may include hls.js-injected tracks).
     */
    myTextTracks = [];

    tracks.forEach(function (track) {
      var el       = document.createElement("track");
      el.kind      = "subtitles";
      el.label     = track.name;
      el.srclang   = track.language;
      el.src       = "/hls/" + VIDEO_ID + "/sub_" + track.index + ".vtt";
      el.default   = false;
      videoEl.appendChild(el);
      myTextTracks.push(el.track);
    });

    /* Ensure all tracks start as disabled (browser may auto-enable one) */
    myTextTracks.forEach(function (t) {
      t.mode = "disabled";
    });

    /* Populate <select>: first option is "Off" */
    subSelect.innerHTML = '<option value="-1">Off</option>';
    tracks.forEach(function (track) {
      var opt         = document.createElement("option");
      opt.value       = track.index;
      opt.textContent = track.name;
      subSelect.appendChild(opt);
    });

    subSelector.style.display = "";

    subSelect.addEventListener("change", function () {
      var val = parseInt(this.value, 10);

      /* Disable all our subtitle tracks */
      myTextTracks.forEach(function (t) {
        t.mode = "disabled";
      });

      /* Enable the selected one */
      if (val >= 0 && myTextTracks[val]) {
        myTextTracks[val].mode = "showing";
        console.log("[Player] Subtitle track enabled:", val,
                    myTextTracks[val].label);
      } else {
        console.log("[Player] Subtitles off");
      }
    });
  }

  /* ==========================================================
     HLS INITIALISATION
  ========================================================== */

  function initHLS(url) {
    if (!url) {
      showOverlay("Server did not return a stream URL.", true);
      setStatus("No stream URL", "error");
      return;
    }

    if (typeof Hls === "undefined") {
      if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
        videoEl.src = url;
        setStatus("Playing (native HLS)", "active");
      } else {
        showOverlay(
          "hls.js was not loaded. See README.md \u2192 Installation \u2192 HLS.js.",
          true
        );
        setStatus("hls.js missing", "error");
      }
      return;
    }

    if (Hls.isSupported()) {
      hlsInstance = new Hls({
        enableWorker:       true,
        maxBufferLength:    30,
        maxMaxBufferLength: 90,
        lowLatencyMode:     false,
      });

      hlsInstance.loadSource(url);
      hlsInstance.attachMedia(videoEl);

      hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
        setStatus("Ready", "active");
      });

      hlsInstance.on(Hls.Events.AUDIO_TRACK_SWITCHED, function (event, data) {
        audioSelect.value = data.id;
      });

      hlsInstance.on(Hls.Events.ERROR, function (event, data) {
        console.warn("[Player] HLS error:", data.type, data.details, data);
        if (!data.fatal) return;

        switch (data.type) {
          case Hls.ErrorTypes.NETWORK_ERROR:
            setStatus("Network error \u2014 retrying\u2026", "loading");
            hlsInstance.startLoad();
            break;

          case Hls.ErrorTypes.MEDIA_ERROR:
            setStatus("Media error \u2014 recovering\u2026", "loading");
            hlsInstance.recoverMediaError();
            break;

          default:
            showOverlay(
              "Playback error: " + data.details +
              ".\nOpen browser DevTools console for details.",
              true
            );
            setStatus("Playback error: " + data.details, "error");
            hlsInstance.destroy();
            hlsInstance = null;
        }
      });

    } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
      videoEl.src = url;
      setStatus("Playing (native HLS)", "active");

    } else {
      showOverlay(
        "Your browser does not support HLS playback.\nUse Chrome or Firefox.",
        true
      );
      setStatus("Browser unsupported", "error");
    }
  }

  /* ==========================================================
     START
  ========================================================== */

  startPolling();

}());
