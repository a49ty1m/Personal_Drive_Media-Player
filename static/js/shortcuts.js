/* ============================================================
   shortcuts.js — VLC-style keyboard shortcut system
   Termux Media Server

   Implements the full VLC keyboard shortcut set plus OSD
   (on-screen display) notifications for every action.
   ============================================================ */

(function () {
  "use strict";

  /* ----------------------------------------------------------
     Wait for DOM + player to be ready
  ---------------------------------------------------------- */
  window.addEventListener("DOMContentLoaded", function () {
    initShortcuts();
  });

  /* ----------------------------------------------------------
     OSD (On-Screen Display) — imported from utils.js
  ---------------------------------------------------------- */
  // Using showOSD() from utils.js for consistency

  /* ----------------------------------------------------------
     Shortcut help panel
  ---------------------------------------------------------- */
  var helpVisible = false;

  var SHORTCUT_GROUPS = [
    {
      label: "Playback",
      shortcuts: [
        { keys: ["Space"], desc: "Play / Pause" },
        { keys: ["P"], desc: "Play / Pause (alternate)" },
        { keys: ["S"], desc: "Stop" },
        { keys: ["."], desc: "Next frame (when paused)" },
        { keys: ["E"], desc: "Next frame (alternate)" },
      ],
    },
    {
      label: "Navigation",
      shortcuts: [
        { keys: ["→"], desc: "Seek forward 10 s" },
        { keys: ["←"], desc: "Seek backward 10 s" },
        { keys: ["Shift + →"], desc: "Seek forward 10 s" },
        { keys: ["Shift + ←"], desc: "Seek backward 10 s" },
        { keys: ["Ctrl + →"], desc: "Seek forward 10 s" },
        { keys: ["Ctrl + ←"], desc: "Seek backward 10 s" },
        { keys: ["Alt + →"], desc: "Seek forward 10 s" },
        { keys: ["Alt + ←"], desc: "Seek backward 10 s" },
      ],
    },
    {
      label: "Volume",
      shortcuts: [
        { keys: ["↑"], desc: "Volume up 5 %" },
        { keys: ["↓"], desc: "Volume down 5 %" },
        { keys: ["Ctrl + ↑"], desc: "Volume up 10 %" },
        { keys: ["Ctrl + ↓"], desc: "Volume down 10 %" },
        { keys: ["M"], desc: "Mute / Unmute" },
      ],
    },
    {
      label: "Speed",
      shortcuts: [
        { keys: ["+"], desc: "Speed up (×1.1)" },
        { keys: ["-"], desc: "Speed down (×0.9)" },
        { keys: ["="], desc: "Normal speed (×1.0)" },
        { keys: ["]"], desc: "Speed up slightly" },
        { keys: ["["], desc: "Speed down slightly" },
        { keys: ["Shift + ="], desc: "Normal speed" },
      ],
    },
    {
      label: "Display",
      shortcuts: [
        { keys: ["F"], desc: "Toggle fullscreen" },
        { keys: ["F11"], desc: "Toggle fullscreen (alternate)" },
        { keys: ["Esc"], desc: "Exit fullscreen / Close help" },
        { keys: ["Z"], desc: "Cycle aspect ratios" },
        { keys: ["T"], desc: "Toggle always-on-top (Web: PiP)" },
      ],
    },
    {
      label: "Tracks",
      shortcuts: [
        { keys: ["V"], desc: "Cycle subtitle tracks" },
        { keys: ["B"], desc: "Cycle audio tracks" },
        { keys: ["G"], desc: "Subtitle delay −50 ms" },
        { keys: ["H"], desc: "Subtitle delay +50 ms" },
        { keys: ["J"], desc: "Audio delay −50 ms" },
        { keys: ["K"], desc: "Audio delay +50 ms" },
      ],
    },
    {
      label: "Other",
      shortcuts: [
        { keys: ["?", "Shift + /"], desc: "Show / hide this help" },
        { keys: ["I"], desc: "Show media info OSD" },
        { keys: ["O"], desc: "Show OSD toggle info" },
        { keys: ["R"], desc: "Loop / repeat mode" },
      ],
    },
  ];

  function createHelpPanel() {
    if (document.getElementById("vlc-help")) return;

    var panel = document.createElement("div");
    panel.id = "vlc-help";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Keyboard shortcuts");

    var header = document.createElement("div");
    header.className = "help-header";

    var title = document.createElement("h2");
    title.className = "help-title";
    title.innerHTML = "⌨️ Keyboard Shortcuts";

    var closeBtn = document.createElement("button");
    closeBtn.className = "help-close";
    closeBtn.textContent = "×";
    closeBtn.setAttribute("aria-label", "Close shortcuts");
    closeBtn.addEventListener("click", function () { toggleHelp(false); });

    header.appendChild(title);
    header.appendChild(closeBtn);
    panel.appendChild(header);

    var subtitle = document.createElement("p");
    subtitle.className = "help-subtitle";
    subtitle.textContent = "All VLC keyboard shortcuts implemented in your browser.";
    panel.appendChild(subtitle);

    var grid = document.createElement("div");
    grid.className = "help-grid";

    SHORTCUT_GROUPS.forEach(function (group) {
      var groupEl = document.createElement("div");
      groupEl.className = "help-group";

      var groupLabel = document.createElement("div");
      groupLabel.className = "help-group-label";
      groupLabel.textContent = group.label;
      groupEl.appendChild(groupLabel);

      group.shortcuts.forEach(function (sc) {
        var row = document.createElement("div");
        row.className = "help-row";

        var keysEl = document.createElement("div");
        keysEl.className = "help-keys";
        sc.keys.forEach(function (k) {
          var kbd = document.createElement("kbd");
          kbd.textContent = k;
          keysEl.appendChild(kbd);
        });

        var descEl = document.createElement("div");
        descEl.className = "help-desc";
        descEl.textContent = sc.desc;

        row.appendChild(keysEl);
        row.appendChild(descEl);
        groupEl.appendChild(row);
      });

      grid.appendChild(groupEl);
    });

    panel.appendChild(grid);

    var backdrop = document.createElement("div");
    backdrop.id = "vlc-help-backdrop";
    backdrop.addEventListener("click", function () { toggleHelp(false); });

    document.body.appendChild(backdrop);
    document.body.appendChild(panel);
  }

  function toggleHelp(force) {
    createHelpPanel();
    var panel    = document.getElementById("vlc-help");
    var backdrop = document.getElementById("vlc-help-backdrop");

    if (typeof force !== "undefined") {
      helpVisible = force;
    } else {
      helpVisible = !helpVisible;
    }

    if (helpVisible) {
      panel.classList.add("help-open");
      backdrop.classList.add("help-open");
      panel.focus();
    } else {
      panel.classList.remove("help-open");
      backdrop.classList.remove("help-open");
    }
  }

  /* ----------------------------------------------------------
     Shortcut state
  ---------------------------------------------------------- */
  var aspectRatios  = ["", "16/9", "4/3", "1/1", "21/9", "9/16"];
  var aspectIndex   = 0;
  var loopMode      = 0;         // 0=none, 1=loop-all (single video only)
  var subDelayMs    = 0;         // accumulated subtitle delay (display only)
  var audioDelayMs  = 0;         // accumulated audio delay (display only)

  /* ----------------------------------------------------------
     Helpers
  ---------------------------------------------------------- */
  function getVideo() {
    return window.__playerVideo || document.getElementById("video-player");
  }

  function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
  }

  function fmtTime(secs) {
    var s = Math.floor(Math.abs(secs));
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var ss = s % 60;
    var sign = secs < 0 ? "-" : "";
    if (h > 0) {
      return sign + h + ":" + String(m).padStart(2, "0") + ":" + String(ss).padStart(2, "0");
    }
    return sign + m + ":" + String(ss).padStart(2, "0");
  }

  function pct(val) {
    return Math.round(val * 100) + "%";
  }

  function speedStr(r) {
    return r.toFixed(2) + "×";
  }

  /* ----------------------------------------------------------
     Actions
  ---------------------------------------------------------- */

  function actionPlayPause(video) {
    if (video.paused || video.ended) {
      video.play();
      showOSD("▶", "Play");
    } else {
      video.pause();
      showOSD("⏸", "Pause");
    }
  }

  function actionStop(video) {
    video.pause();
    video.currentTime = 0;
    showOSD("⏹", "Stop");
  }

  function actionSeek(video, deltaSec) {
    var newTime = clamp(video.currentTime + deltaSec, 0, video.duration || 0);
    video.currentTime = newTime;
    var dir = deltaSec > 0 ? "⏩" : "⏪";
    var sign = deltaSec > 0 ? "+" : "";
    showOSD(dir, sign + deltaSec + "s  " + fmtTime(newTime));
  }

  function actionVolume(video, delta) {
    video.volume = clamp(video.volume + delta, 0, 1);
    var icon = video.volume === 0 ? "🔇" : video.volume < 0.5 ? "🔉" : "🔊";
    showOSD(icon, "Volume " + pct(video.volume));
  }

  function actionMute(video) {
    video.muted = !video.muted;
    showOSD(video.muted ? "🔇" : "🔊", video.muted ? "Muted" : "Unmuted");
  }

  function actionSpeed(video, factor) {
    var r = clamp(video.playbackRate * factor, 0.1, 16);
    video.playbackRate = Math.round(r * 100) / 100;
    showOSD("⚡", "Speed " + speedStr(video.playbackRate));
  }

  function actionSetSpeed(video, rate) {
    video.playbackRate = rate;
    showOSD("⚡", "Speed " + speedStr(rate));
  }

  function actionSpeedStep(video, step) {
    // Additive step like VLC uses with [ and ]
    var r = clamp(video.playbackRate + step, 0.1, 16);
    video.playbackRate = Math.round(r * 100) / 100;
    showOSD("⚡", "Speed " + speedStr(video.playbackRate));
  }

  function actionNextFrame(video) {
    if (!video.paused) video.pause();
    // Advance by one frame ≈ 1/30 s
    video.currentTime = Math.min(video.currentTime + 1 / 30, video.duration || 0);
    showOSD("⏭", "Frame →  " + fmtTime(video.currentTime));
  }

  function actionFullscreen(video) {
    if (!document.fullscreenElement &&
        !document.webkitFullscreenElement &&
        !document.mozFullScreenElement) {
      /* Prefer fullscreen on the video element itself — gives the
         cleanest result (just the video, no page chrome).  Fall back
         to the wrapper div if the video element refuses. */
      var target = video || document.querySelector(".player-wrapper");
      var req = target.requestFullscreen ||
                target.webkitRequestFullscreen ||
                target.mozRequestFullScreen ||
                target.msRequestFullscreen;
      if (req) {
        req.call(target).catch(function () {
          /* If video element refused, try the wrapper */
          var wrapper = document.querySelector(".player-wrapper");
          if (wrapper && wrapper !== target) {
            var req2 = wrapper.requestFullscreen ||
                       wrapper.webkitRequestFullscreen ||
                       wrapper.mozRequestFullScreen;
            if (req2) req2.call(wrapper);
          }
        });
      }
      showOSD("⛶", "Fullscreen");
    } else {
      var exit = document.exitFullscreen ||
                 document.webkitExitFullscreen ||
                 document.mozCancelFullScreen ||
                 document.msExitFullscreen;
      if (exit) exit.call(document);
      showOSD("⊡", "Exit fullscreen");
    }
  }

  function actionPiP(video) {
    if (document.pictureInPictureEnabled) {
      if (document.pictureInPictureElement) {
        document.exitPictureInPicture();
        showOSD("🪟", "Exit Picture-in-Picture");
      } else {
        video.requestPictureInPicture();
        showOSD("🪟", "Picture-in-Picture");
      }
    } else {
      showOSD("⚠", "PiP not supported");
    }
  }

  function actionAspectRatio(video) {
    aspectIndex = (aspectIndex + 1) % aspectRatios.length;
    var ratio = aspectRatios[aspectIndex];
    video.style.aspectRatio = ratio;
    video.style.objectFit = ratio ? "fill" : "";
    var label = ratio || "Default";
    showOSD("🎞", "Aspect ratio: " + label);
  }

  function actionCycleSubtitles() {
    // Work with the sub-track select element
    var sel = document.getElementById("sub-track");
    if (!sel || sel.options.length === 0) {
      showOSD("💬", "No subtitles available");
      return;
    }
    var nextIdx = (sel.selectedIndex + 1) % sel.options.length;
    sel.selectedIndex = nextIdx;
    sel.dispatchEvent(new Event("change"));
    var label = sel.options[nextIdx].text;
    showOSD("💬", "Subtitles: " + label);
  }

  function actionCycleAudio() {
    var sel = document.getElementById("audio-track");
    if (!sel || sel.options.length === 0) {
      showOSD("🎵", "Single audio track");
      return;
    }
    var nextIdx = (sel.selectedIndex + 1) % sel.options.length;
    sel.selectedIndex = nextIdx;
    sel.dispatchEvent(new Event("change"));
    var label = sel.options[nextIdx].text;
    showOSD("🎵", "Audio: " + label);
  }

  function actionSubDelay(delta) {
    subDelayMs += delta;
    showOSD("💬", "Subtitle delay: " + subDelayMs + " ms");
  }

  function actionAudioDelay(delta) {
    audioDelayMs += delta;
    showOSD("🎵", "Audio delay: " + audioDelayMs + " ms");
  }

  function actionLoopMode(video) {
    loopMode = (loopMode + 1) % 2;
    video.loop = loopMode === 1;
    var labels = ["No repeat", "Repeat one"];
    showOSD("🔁", labels[loopMode]);
  }

  function actionMediaInfo(video) {
    var dur = isNaN(video.duration) ? "?" : fmtTime(video.duration);
    var pos = fmtTime(video.currentTime);
    var info = pos + " / " + dur + "  ·  " + speedStr(video.playbackRate) +
               "  ·  Vol " + pct(video.volume);
    showOSD("ℹ", info);
  }

  /* ----------------------------------------------------------
     Key handler
     -------------------------------------------------------
     IMPORTANT: we register in CAPTURE phase (third arg = true)
     so our handler runs BEFORE the browser's built-in
     <video controls> keyboard handler (which lives on the
     element in the bubble phase).  Without this, Space/Arrow
     keys fire twice — once by us and once by the native
     controls — causing double-seeks, double-toggles, etc.
  ---------------------------------------------------------- */

  /* Keys we own completely — always block native behaviour */
  var OWNED_KEYS = new Set([
    " ", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
    "f", "F", "F11", "m", "M", "p", "P", "s", "S",
    ".", "e", "E", "+", "-", "=", "]", "[",
    "t", "T", "z", "Z", "v", "V", "b", "B",
    "g", "G", "h", "H", "j", "J", "k", "K",
    "r", "R", "i", "I", "o", "O", "?", "/"
  ]);

  function handleKey(e) {
    /* Never intercept when typing in form controls */
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;

    var video = getVideo();
    if (!video) return;

    var key  = e.key;
    var ctrl = e.ctrlKey;
    var alt  = e.altKey;
    var meta = e.metaKey;
    var shift = e.shiftKey;

    /* Block all owned keys from reaching the native video handler */
    if (OWNED_KEYS.has(key) && !meta) {
      e.preventDefault();
      e.stopPropagation();
    }

    /* ---- Help panel ---- */
    if ((key === "?" || (key === "/" && shift)) && !ctrl && !alt && !meta) {
      toggleHelp();
      return;
    }

    /* ---- Escape ---- */
    if (key === "Escape") {
      if (helpVisible) { toggleHelp(false); }
      else if (document.fullscreenElement) { document.exitFullscreen(); }
      return;
    }

    switch (key) {

      /* ---- Play / Pause / Stop ---- */
      case " ":
        if (!ctrl && !alt) actionPlayPause(video);
        break;

      case "p": case "P":
        if (!ctrl && !alt) actionPlayPause(video);
        break;

      case "s": case "S":
        if (!ctrl && !alt) actionStop(video);
        break;

      /* ---- Frame step ---- */
      case ".":
        if (!ctrl && !alt) actionNextFrame(video);
        break;

      case "e": case "E":
        if (!ctrl && !alt && !shift) actionNextFrame(video);
        break;

      /* ---- Seek (always 10 s) ---- */
      case "ArrowRight":
        actionSeek(video, 10);
        break;

      case "ArrowLeft":
        actionSeek(video, -10);
        break;

      /* ---- Volume ---- */
      case "ArrowUp":
        if (ctrl && !shift && !alt) actionVolume(video, 0.10);
        else if (!ctrl && !shift && !alt) actionVolume(video, 0.05);
        break;

      case "ArrowDown":
        if (ctrl && !shift && !alt) actionVolume(video, -0.10);
        else if (!ctrl && !shift && !alt) actionVolume(video, -0.05);
        break;

      case "m": case "M":
        if (!ctrl && !alt) actionMute(video);
        break;

      /* ---- Speed ---- */
      case "+":
        if (!ctrl && !alt) actionSpeed(video, 1.1);
        break;

      case "-":
        if (!ctrl && !alt) actionSpeed(video, 0.9);
        break;

      case "=":
        if (!ctrl && !alt) actionSetSpeed(video, 1.0);
        break;

      case "]":
        if (!ctrl && !alt) actionSpeedStep(video, 0.1);
        break;

      case "[":
        if (!ctrl && !alt) actionSpeedStep(video, -0.1);
        break;

      /* ---- Fullscreen ---- */
      case "f": case "F":
        if (!ctrl && !alt) actionFullscreen(video);
        break;

      case "F11":
        actionFullscreen(video);
        break;

      /* ---- Picture-in-Picture ---- */
      case "t": case "T":
        if (!ctrl && !alt) actionPiP(video);
        break;

      /* ---- Aspect Ratio ---- */
      case "z": case "Z":
        if (!ctrl && !alt) actionAspectRatio(video);
        break;

      /* ---- Subtitles ---- */
      case "v": case "V":
        if (!ctrl && !alt) actionCycleSubtitles();
        break;

      case "g": case "G":
        if (!ctrl && !alt) actionSubDelay(-50);
        break;

      case "h": case "H":
        if (!ctrl && !alt) actionSubDelay(+50);
        break;

      /* ---- Audio ---- */
      case "b": case "B":
        if (!ctrl && !alt) actionCycleAudio();
        break;

      case "j": case "J":
        if (!ctrl && !alt) actionAudioDelay(-50);
        break;

      case "k": case "K":
        if (!ctrl && !alt) actionAudioDelay(+50);
        break;

      /* ---- Loop ---- */
      case "r": case "R":
        if (!ctrl && !alt) actionLoopMode(video);
        break;

      /* ---- Media info ---- */
      case "i": case "I":
        if (!ctrl && !alt) actionMediaInfo(video);
        break;

      /* ---- OSD info ---- */
      case "o": case "O":
        if (!ctrl && !alt) showOSD("ℹ", "VLC shortcuts active — press ? for help");
        break;

      default:
        break;
    }
  }

  function initShortcuts() {
    /*
     * Capture phase (true) = runs BEFORE the browser's built-in
     * <video controls> keyboard handler, which lives in bubble phase.
     * This prevents double-seek / double-toggle bugs.
     */
    document.addEventListener("keydown", handleKey, true);

    /*
     * Belt-and-suspenders: also intercept directly on the video element
     * in capture phase so even if focus is inside the shadow DOM of the
     * native controls, our handler wins.
     */
    var video = getVideo();
    if (video) {
      video.addEventListener("keydown", handleKey, true);

      video.addEventListener("loadedmetadata", function () {
        showOSD("⌨", "Press ? for shortcuts");
      }, { once: true });
    }

    // Add floating help button to player
    addHelpButton();
  }


  /* ----------------------------------------------------------
     Help button — small "?" button on the player wrapper
  ---------------------------------------------------------- */
  function addHelpButton() {
    var wrapper = document.querySelector(".player-wrapper");
    if (!wrapper || document.getElementById("vlc-help-btn")) return;

    var btn = document.createElement("button");
    btn.id = "vlc-help-btn";
    btn.textContent = "?";
    btn.title = "Keyboard shortcuts (?)";
    btn.setAttribute("aria-label", "Show keyboard shortcuts");
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleHelp();
    });
    wrapper.appendChild(btn);
  }

}());
