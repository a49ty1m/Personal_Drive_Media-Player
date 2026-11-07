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
  var osdEl         = document.getElementById("vlc-osd");
  var osdIcon       = osdEl ? osdEl.querySelector(".osd-icon") : null;
  var osdText       = osdEl ? osdEl.querySelector(".osd-text") : null;

  /* ----------------------------------------------------------
     Config
  ---------------------------------------------------------- */
  var VIDEO_ID      = videoEl.dataset.videoId;
  var POLL_INTERVAL = 1500;
  var MAX_NET_ERRS  = 6;
  var SAVE_INTERVAL = 5000;  // Save position every 5 seconds

  /* ----------------------------------------------------------
     State
  ---------------------------------------------------------- */
  var pollTimer     = null;
  var hlsInstance   = null;
  var netErrCount   = 0;
  var myTextTracks  = [];   // TextTrack objects for our subtitle tracks
  var saveTimer     = null;  // Timer for saving position
  var osdTimer      = null;  // Timer for OSD auto-hide

  /* ==========================================================
     OSD (ON-SCREEN DISPLAY) - VLC-style notifications
  ========================================================== */

  function showOSD(icon, text) {
    if (!osdEl || !osdIcon || !osdText) return;
    
    // Clear any existing timer
    if (osdTimer) {
      clearTimeout(osdTimer);
      osdTimer = null;
    }
    
    // Set content
    osdIcon.textContent = icon;
    osdText.textContent = text;
    
    // Show with animation
    osdEl.classList.remove("osd-fade");
    osdEl.classList.add("osd-visible");
    
    // Auto-hide after 1.2 seconds (matching shortcuts.js timing)
    osdTimer = setTimeout(function() {
      osdEl.classList.add("osd-fade");
      setTimeout(function() {
        osdEl.classList.remove("osd-visible", "osd-fade");
      }, 500);
    }, 1200);
  }

  // Expose showOSD globally so shortcuts.js can use it too
  window.showOSD = showOSD;

  /* ==========================================================
     POSITION SAVING & RESUME
  ========================================================== */

  function getStorageKey() {
    return "video-position-" + VIDEO_ID;
  }

  function getSavedPosition() {
    try {
      var saved = localStorage.getItem(getStorageKey());
      if (saved) {
        var data = JSON.parse(saved);
        // Only resume if saved within last 7 days
        var age = Date.now() - data.timestamp;
        if (age < 7 * 24 * 60 * 60 * 1000) {
          return data.position;
        }
      }
    } catch (e) {
      console.warn("[Player] Could not load saved position:", e);
    }
    return 0;
  }

  function savePosition() {
    if (!videoEl || videoEl.paused) return;
    
    try {
      var position = videoEl.currentTime;
      var duration = videoEl.duration;
      
      // Don't save if at the very end (within last 30 seconds)
      if (duration && position > duration - 30) {
        localStorage.removeItem(getStorageKey());
        return;
      }
      
      // Don't save positions less than 10 seconds
      if (position < 10) return;
      
      localStorage.setItem(getStorageKey(), JSON.stringify({
        position: position,
        timestamp: Date.now()
      }));
      
      console.log("[Player] Saved position:", Math.floor(position), "seconds");
    } catch (e) {
      console.warn("[Player] Could not save position:", e);
    }
  }

  function startPositionSaving() {
    // Save position every 5 seconds while playing
    saveTimer = setInterval(function() {
      if (!videoEl.paused) {
        savePosition();
      }
    }, SAVE_INTERVAL);
    
    // Also save on pause and when leaving page
    videoEl.addEventListener("pause", savePosition);
    window.addEventListener("beforeunload", savePosition);
  }

  function stopPositionSaving() {
    if (saveTimer) {
      clearInterval(saveTimer);
      saveTimer = null;
    }
  }

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
      if (!isNaN(idx)) {
        hlsInstance.audioTrack = idx;
        var trackName = audioSelect.options[audioSelect.selectedIndex].text;
        showOSD("🎵", "Audio: " + trackName);
      }
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
        var trackName = subSelect.options[subSelect.selectedIndex].text;
        showOSD("💬", "Subtitle: " + trackName);
        console.log("[Player] Subtitle track enabled:", val,
                    myTextTracks[val].label);
      } else {
        showOSD("💬", "Subtitle: Off");
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
        resumeFromSavedPosition();
        startPositionSaving();
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
      var savedPosition = getSavedPosition();
      
      // ANTI-STUTTER buffering for 1080p mobile
      hlsInstance = new Hls({
        enableWorker:       true,
        
        // Larger buffers to absorb encoding delays
        maxBufferLength:    30,    // Keep 30 seconds buffered
        maxMaxBufferLength: 60,    // Max 60s buffer
        maxBufferSize:      60 * 1000 * 1000,  // 60MB max (tolerate large segments)
        maxBufferHole:      0.3,   // Small gaps OK
        
        // Network optimization
        lowLatencyMode:     false,
        backBufferLength:   5,     // Keep only 5s behind (save memory)
        
        // Quality & performance
        abrEwmaDefaultEstimate: 5000000,  // Assume good bandwidth
        startPosition:      savedPosition,
        
        // Aggressive fragment loading (no stutters from network delays)
        manifestLoadingTimeOut: 15000,
        manifestLoadingMaxRetry: 4,
        levelLoadingTimeOut: 15000,
        levelLoadingMaxRetry: 4,
        fragLoadingTimeOut: 30000,  // 30s timeout for large segments
        fragLoadingMaxRetry: 6,
        
        // Start loading immediately
        startFragPrefetch: true,
        testBandwidth: false,  // Don't waste time measuring
      });

      hlsInstance.loadSource(url);
      hlsInstance.attachMedia(videoEl);

      hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
        setStatus("Ready", "active");
        
        if (savedPosition > 0) {
          console.log("[Player] Resuming from", Math.floor(savedPosition), "seconds");
          showOverlay("Resuming from " + formatTime(savedPosition) + "\u2026");
          
          // Hide overlay after video starts playing
          videoEl.addEventListener("playing", function() {
            setTimeout(hideOverlay, 500);
          }, { once: true });
        }
        
        startPositionSaving();
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
            stopPositionSaving();
            hlsInstance.destroy();
            hlsInstance = null;
        }
      });

    } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
      videoEl.src = url;
      setStatus("Playing (native HLS)", "active");
      resumeFromSavedPosition();
      startPositionSaving();

    } else {
      showOverlay(
        "Your browser does not support HLS playback.\nUse Chrome or Firefox.",
        true
      );
      setStatus("Browser unsupported", "error");
    }
  }

  function resumeFromSavedPosition() {
    var savedPosition = getSavedPosition();
    if (savedPosition > 0) {
      console.log("[Player] Resuming from", Math.floor(savedPosition), "seconds");
      videoEl.currentTime = savedPosition;
      showOverlay("Resuming from " + formatTime(savedPosition) + "\u2026");
      videoEl.addEventListener("playing", function() {
        setTimeout(hideOverlay, 500);
      }, { once: true });
    }
  }

  function formatTime(seconds) {
    var mins = Math.floor(seconds / 60);
    var secs = Math.floor(seconds % 60);
    return mins + ":" + (secs < 10 ? "0" : "") + secs;
  }

  /* ==========================================================
     START
  ========================================================== */

  startPolling();

}());
