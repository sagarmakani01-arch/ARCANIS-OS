import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    clip: true

    signal appClicked(string appName, string appLabel)

    property var apps: [
        { name: "terminal", label: "Terminal", icon: "\u{1F4BB}", color: "#0066cc" },
        { name: "filesystem", label: "Files", icon: "\u{1F4C1}", color: "#0078d4" },
        { name: "settings", label: "Settings", icon: "\u2699\uFE0F", color: "#5c5c5c" },
        { name: "system", label: "System Info", icon: "\u{1F4CA}", color: "#0066cc" },
        { name: "network", label: "Network", icon: "\u{1F310}", color: "#0078d4" },
        { name: "processes", label: "Processes", icon: "\u269B", color: "#5c5c5c" },
        { name: "applications", label: "Apps", icon: "\u{1F4E6}", color: "#0066cc" },
        { name: "trash", label: "Trash", icon: "\u{1F5D1}\uFE0F", color: "#999999" }
    ]

    GridView {
        id: grid
        anchors.fill: parent
        anchors { topMargin: 30; leftMargin: 24; rightMargin: 24; bottomMargin: 24 }
        cellWidth: 100
        cellHeight: 110
        interactive: false
        model: apps

        delegate: Item {
            width: grid.cellWidth
            height: grid.cellHeight

            Rectangle {
                id: iconBg
                anchors.centerIn: parent
                width: 52
                height: 52
                radius: 14
                color: "#ffffff"
                border.color: "#d4d8dd"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: modelData.icon
                    font.pixelSize: 22
                }

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: {
                        iconBg.color = "#e5f0ff"
                        iconBg.border.color = "#0066cc"
                    }
                    onExited: {
                        iconBg.color = "#ffffff"
                        iconBg.border.color = "#d4d8dd"
                    }
                }
            }

            Text {
                anchors { top: iconBg.bottom; topMargin: 6; horizontalCenter: parent.horizontalCenter }
                text: modelData.label
                color: "#1a1a1a"
                font.pixelSize: 10
                font.family: "Segoe UI"
            }
        }
    }
}
