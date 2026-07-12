#!/bin/sh
# Launch the Digital logic simulator with the bundled portable JRE.
# No system Java or root needed. Opens the circuits in this folder.
#
# The app (Digital.jar + a portable Java 17 runtime) lives OUTSIDE this repo,
# in ~/.local/share/digital-app, so Digital doesn't scan it for components and
# clash with your circuit names.
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$HOME/.local/share/digital-app"
JAVA="$APP/jdk-17.0.19+10-jre/bin/java"

# Sway/i3/dwm and other tiling WMs don't reparent windows, which makes Java
# Swing windows render blank/white and never paint. This tells AWT to cope.
export _JAVA_AWT_WM_NONREPARENTING=1
# Force the X11 (XWayland) toolkit and software pipeline for reliable painting.
export AWT_TOOLKIT=XToolkit

# On XWayland (Sway) Java's pointer grab for menus/dialogs can get stuck, so
# after the first dialog the main window stops accepting clicks. Disable grabs.
#
# Lag fix: opengl=false means pure software rendering (every redraw is CPU-drawn
# then pushed through XWayland) -> sluggish pan/zoom on big sheets like CPU.dig.
# xrender=true uses X11's accelerated 2D pipeline instead; keeps the blank-window
# fix (that's _JAVA_AWT_WM_NONREPARENTING, not the opengl flag). If it ever paints
# blank again, drop -Dsun.java2d.xrender=true back to -Dsun.java2d.opengl=false.
exec "$JAVA" \
    -Xmx2g \
    -Dsun.java2d.xrender=true \
    -Dsun.awt.disablegrab=true \
    -Dawt.useSystemAAFontSettings=on \
    -Dswing.aatext=true \
    -jar "$APP/Digital/Digital.jar" "$@"
