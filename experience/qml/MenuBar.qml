import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    height: 32
    color: "#ffffff"
    z: 999

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "#d4d8dd"
    }

    RowLayout {
        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
        spacing: 20

        Text {
            text: "\u2318 ARCANIS"
            color: "#1a1a1a"
            font.pixelSize: 11
            font.bold: true
            font.family: "Segoe UI"
        }

        Repeater {
            model: ["OS", "File", "Edit", "View", "Terminal", "Help"]
            Text {
                text: modelData
                color: "#666666"
                font.pixelSize: 10
                font.family: "Segoe UI"
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: parent.color = "#1a1a1a"
                    onExited: parent.color = "#666666"
                }
            }
        }
    }

    RowLayout {
        anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
        spacing: 14

        Text {
            text: "\u{1F310}"
            color: "#999999"
            font.pixelSize: 11
        }

        Text {
            id: clockLabel
            text: "00:00"
            color: "#1a1a1a"
            font.pixelSize: 11
            font.family: "Segoe UI"

            Timer {
                interval: 1000
                repeat: true
                running: true
                onTriggered: {
                    var d = new Date()
                    var h = d.getHours().toString().padStart(2, "0")
                    var m = d.getMinutes().toString().padStart(2, "0")
                    clockLabel.text = h + ":" + m
                }
            }
        }
    }
}
