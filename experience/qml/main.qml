import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    visible: true
    color: "#e8ecf0"
    flags: Qt.FramelessWindowHint | Qt.Window
    visibility: Window.FullScreen

    property bool bootDone: false
    property real bootProgress: 0.0
    property var openWindows: []

    Timer {
        interval: 16
        repeat: true
        running: true
        onTriggered: {
            if (!bootDone) {
                bootProgress = Math.min(1.0, bootProgress + 0.006)
                if (bootProgress >= 1.0) {
                    bootDone = true
                }
            }
        }
    }

    Timer {
        id: bootTimer
        interval: 1800
        running: true
        onTriggered: { bootDone = true }
    }

    Rectangle {
        anchors.fill: parent
        color: "#e8ecf0"
    }

    Rectangle {
        anchors.fill: parent
        color: "#e8ecf0"
        visible: !bootDone
        z: 9999

        Column {
            anchors.centerIn: parent
            spacing: 16

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "ARCANIS"
                color: "#1a1a1a"
                font.pixelSize: 36
                font.bold: true
                font.family: "Segoe UI"
                font.letterSpacing: 4
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "OPERATING SYSTEM"
                color: "#666666"
                font.pixelSize: 10
                font.family: "Segoe UI"
                font.letterSpacing: 3
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 200
                height: 2
                color: "#d4d8dd"
                radius: 1

                Rectangle {
                    width: parent.width * root.bootProgress
                    height: parent.height
                    color: "#0066cc"
                    radius: 1
                    Behavior on width { SmoothedAnimation { duration: 80 } }
                }
            }
        }
    }

    MenuBar {
        id: menuBar
        anchors { top: parent.top; left: parent.left; right: parent.right }
        visible: bootDone
    }

    DesktopGrid {
        id: desktopGrid
        anchors { top: menuBar.bottom; left: parent.left; right: parent.right; bottom: dockContainer.top }
        visible: bootDone
        onAppClicked: openApp(appName, appLabel)
    }

    Item {
        id: dockContainer
        anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
        height: 72
        visible: bootDone

        Dock {
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 6 }
            width: Math.min(parent.width - 40, 500)
            onDockClicked: openApp(appName, appLabel)
        }
    }

    function openApp(name, label) {
        if (name === "terminal") {
            createTerminalWindow(label)
        } else if (name === "filesystem") {
            createFileSystemWindow(label)
        } else if (name === "settings") {
            createSettingsWindow(label)
        } else if (name === "system") {
            createSystemInfoWindow(label)
        }
    }

    function createTerminalWindow(label) {
        var component = Qt.createComponent("AppWindow.qml")
        if (component.status === Component.Ready) {
            var win = component.createObject(desktopGrid, {
                width: 740, height: 460,
                x: Math.min(60 + Math.random() * 100, desktopGrid.width - 740),
                y: Math.min(40 + Math.random() * 60, desktopGrid.height - 460),
                appName: "terminal", appLabel: label, z: 200
            })
            if (win) {
                win.closeRequested.connect(function() { win.destroy() })
                var termComp = Qt.createComponent("Terminal.qml")
                if (termComp.status === Component.Ready) {
                    termComp.createObject(win.contentArea, { anchors: { fill: win.contentArea } })
                }
                openWindows.push(win)
            }
        }
    }

    function createFileSystemWindow(label) {
        var component = Qt.createComponent("AppWindow.qml")
        if (component.status === Component.Ready) {
            var win = component.createObject(desktopGrid, {
                width: 640, height: 420, x: 120, y: 80,
                appName: "filesystem", appLabel: label, z: 200
            })
            if (win) {
                win.closeRequested.connect(function() { win.destroy() })
                Qt.createQmlObject(
                    'import QtQuick; Rectangle { color: "#ffffff"; ' +
                    '  Text { anchors.centerIn: parent; text: "File System Browser"; color: "#666666"; font.pixelSize: 12; font.family: "Segoe UI" } }',
                    win.contentArea, "fsContent")
                openWindows.push(win)
            }
        }
    }

    function createSettingsWindow(label) {
        var component = Qt.createComponent("AppWindow.qml")
        if (component.status === Component.Ready) {
            var win = component.createObject(desktopGrid, {
                width: 600, height: 400, x: 160, y: 100,
                appName: "settings", appLabel: label, z: 200
            })
            if (win) {
                win.closeRequested.connect(function() { win.destroy() })
                Qt.createQmlObject(
                    'import QtQuick; Rectangle { color: "#ffffff"; ' +
                    '  Text { anchors.centerIn: parent; text: "ARCANIS Settings"; color: "#666666"; font.pixelSize: 12; font.family: "Segoe UI" } }',
                    win.contentArea, "settingsContent")
                openWindows.push(win)
            }
        }
    }

    function createSystemInfoWindow(label) {
        var component = Qt.createComponent("AppWindow.qml")
        if (component.status === Component.Ready) {
            var win = component.createObject(desktopGrid, {
                width: 520, height: 360, x: 180, y: 120,
                appName: "system", appLabel: label, z: 200
            })
            if (win) {
                win.closeRequested.connect(function() { win.destroy() })
                Qt.createQmlObject(
                    'import QtQuick; import QtQuick.Controls; ' +
                    'Rectangle { color: "#ffffff"; ' +
                    '  Column { anchors.centerIn: parent; spacing: 6; ' +
                    '    Text { text: "ARCANIS OS v14.0.0"; color: "#1a1a1a"; font.pixelSize: 14; font.family: "Segoe UI"; font.bold: true } ' +
                    '    Text { text: "Kernel: Windows NT 10.0"; color: "#666666"; font.pixelSize: 11; font.family: "Consolas" } ' +
                    '    Text { text: "Memory: 16 GB"; color: "#666666"; font.pixelSize: 11; font.family: "Consolas" } ' +
                    '    Text { text: "Modules: 126"; color: "#666666"; font.pixelSize: 11; font.family: "Consolas" } ' +
                    '    Text { text: "Commands: 278"; color: "#666666"; font.pixelSize: 11; font.family: "Consolas" } } }',
                    win.contentArea, "sysContent")
                openWindows.push(win)
            }
        }
    }

    Keys.onEscapePressed: Qt.quit()
    Keys.onPressed: {
        if (event.key === Qt.Key_F11) {
            root.visibility = root.visibility === Window.FullScreen ? Window.Windowed : Window.FullScreen
        }
    }
}
