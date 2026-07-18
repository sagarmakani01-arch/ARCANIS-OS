import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    height: 56
    radius: 10
    color: Qt.rgba(1, 1, 1, 0.8)
    border.color: "#d4d8dd"
    border.width: 1
    z: 998

    signal dockClicked(string appName, string appLabel)

    RowLayout {
        anchors.centerIn: parent
        spacing: 4

        Repeater {
            model: [
                { name: "terminal", label: "Terminal", icon: "\u{1F4BB}", color: "#0066cc" },
                { name: "filesystem", label: "Files", icon: "\u{1F4C1}", color: "#0078d4" },
                { name: "settings", label: "Settings", icon: "\u2699\uFE0F", color: "#5c5c5c" },
                { name: "system", label: "System", icon: "\u{1F4CA}", color: "#0066cc" },
                { name: "trash", label: "Trash", icon: "\u{1F5D1}\uFE0F", color: "#999999" }
            ]

            Item {
                width: 44
                height: 44

                Rectangle {
                    anchors.centerIn: parent
                    width: 38; height: 38
                    radius: 8
                    color: "#ffffff"
                    border.color: "#d4d8dd"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: modelData.icon
                        font.pixelSize: 18
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: {
                            parent.color = "#e5f0ff"
                            parent.border.color = "#0066cc"
                        }
                        onExited: {
                            parent.color = "#ffffff"
                            parent.border.color = "#d4d8dd"
                        }
                        onClicked: root.dockClicked(modelData.name, modelData.label)
                    }
                }

                Rectangle {
                    anchors { top: parent.bottom; topMargin: 1; horizontalCenter: parent.horizontalCenter }
                    width: 4; height: 4; radius: 2
                    color: modelData.color
                }
            }
        }
    }

    RowLayout {
        anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
        spacing: 6

        Rectangle {
            width: 1; height: 20
            color: "#d4d8dd"
        }

        Text {
            text: "\u{1F50D}"
            color: "#999999"
            font.pixelSize: 12
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onEntered: parent.color = "#1a1a1a"
                onExited: parent.color = "#999999"
            }
        }
    }
}
