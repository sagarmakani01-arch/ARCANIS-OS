import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    width: 720
    height: 480
    radius: 8
    color: "#ffffff"
    border.color: "#c8ccd0"
    border.width: 1
    clip: true
    z: 100

    property string appName: ""
    property string appLabel: ""
    property bool maximized: false
    property rect savedRect: Qt.rect(0, 0, 720, 480)

    signal closeRequested()

    MouseArea {
        id: dragArea
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 32
        property point clickPos: "0,0"

        onPressed: {
            clickPos = Qt.point(mouse.x, mouse.y)
            if (!root.maximized) {
                root.savedRect = Qt.rect(root.x, root.y, root.width, root.height)
            }
        }
        onPositionChanged: {
            if (!root.maximized && mouse.buttons & Qt.LeftButton) {
                root.x += mouse.x - clickPos.x
                root.y += mouse.y - clickPos.y
            }
        }
        onDoubleClicked: toggleMaximize()
    }

    RowLayout {
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 32
        spacing: 6

        Item { width: 8; height: 1 }

        Row {
            spacing: 6
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                width: 12; height: 12; radius: 6
                color: "#e81123"
                MouseArea {
                    anchors.fill: parent
                    onClicked: root.closeRequested()
                    hoverEnabled: true
                    onEntered: scale = 1.2
                    onExited: scale = 1.0
                }
            }
            Rectangle {
                width: 12; height: 12; radius: 6
                color: "#fecb00"
                MouseArea {
                    anchors.fill: parent
                    onClicked: root.visible = false
                    hoverEnabled: true
                    onEntered: scale = 1.2
                    onExited: scale = 1.0
                }
            }
            Rectangle {
                width: 12; height: 12; radius: 6
                color: "#00cc4b"
                MouseArea {
                    anchors.fill: parent
                    onClicked: toggleMaximize()
                    hoverEnabled: true
                    onEntered: scale = 1.2
                    onExited: scale = 1.0
                }
            }
        }

        Text {
            text: root.appLabel
            color: "#1a1a1a"
            font.pixelSize: 11
            font.family: "Segoe UI"
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            anchors.verticalCenter: parent.verticalCenter
        }

        Item { width: 70; height: 1 }
    }

    Rectangle {
        anchors { top: parent.top; topMargin: 32; left: parent.left; right: parent.right }
        height: 1
        color: "#e8ecf0"
    }

    Item {
        id: contentArea
        anchors { top: parent.top; topMargin: 33; left: parent.left; right: parent.right; bottom: parent.bottom }
    }

    function toggleMaximize() {
        if (root.maximized) {
            root.x = root.savedRect.x; root.y = root.savedRect.y
            root.width = root.savedRect.width; root.height = root.savedRect.height
            root.maximized = false
        } else {
            root.savedRect = Qt.rect(root.x, root.y, root.width, root.height)
            root.x = 0; root.y = 0
            root.width = root.parent ? root.parent.width : 1280
            root.height = root.parent ? root.parent.height : 720
            root.maximized = true
        }
    }
}
