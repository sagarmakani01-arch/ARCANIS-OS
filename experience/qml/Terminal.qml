import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    anchors.fill: parent

    property string prompt: "arcanis@os:~$ "

    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
    }

    Flickable {
        id: flick
        anchors.fill: parent
        anchors.margins: 8
        contentHeight: outputArea.height + inputRow.height + 16

        Column {
            id: outputArea
            width: flick.width
            spacing: 2

            Text {
                text: "ARCANIS OS Terminal [build v14.0.0]"
                color: "#999999"
                font.pixelSize: 11
                font.family: "Consolas"
                bottomPadding: 4
            }

            Text {
                text: "Type 'help' for available commands."
                color: "#999999"
                font.pixelSize: 11
                font.family: "Consolas"
                bottomPadding: 6
            }
        }

        Row {
            id: inputRow
            anchors { top: outputArea.bottom; topMargin: 4 }
            width: flick.width

            Text {
                id: promptLabel
                text: root.prompt
                color: "#0066cc"
                font.pixelSize: 11
                font.family: "Consolas"
            }

            TextInput {
                id: inputField
                width: parent.width - promptLabel.width - 4
                color: "#1a1a1a"
                font.pixelSize: 11
                font.family: "Consolas"
                focus: true
                cursorVisible: true

                property var history: []
                property int historyIndex: -1

                Keys.onReturnPressed: {
                    if (text.trim().length > 0) {
                        executeCommand(text)
                        history.push(text)
                        historyIndex = history.length
                        text = ""
                    }
                }

                Keys.onUpPressed: {
                    if (history.length > 0 && historyIndex > 0) {
                        historyIndex--
                        text = history[historyIndex]
                    }
                }

                Keys.onDownPressed: {
                    if (history.length > 0 && historyIndex < history.length - 1) {
                        historyIndex++
                        text = history[historyIndex]
                    } else {
                        historyIndex = history.length
                        text = ""
                    }
                }
            }
        }
    }

    function executeCommand(cmd) {
        var parts = cmd.trim().split(/\s+/)
        var command = parts[0].toLowerCase()
        var args = parts.slice(1)

        var output = ""

        if (command === "help") {
            output = "  help       Show this help\n  clear      Clear the terminal\n  echo       Echo text\n  date       Show current date and time\n  whoami     Show current user\n  uname      Show OS info\n  ls         List files\n  neofetch   Show system info\n  exit       Close terminal"
        } else if (command === "clear") {
            outputArea.children = []
            return
        } else if (command === "echo") {
            output = args.join(" ")
        } else if (command === "date") {
            output = new Date().toString()
        } else if (command === "whoami") {
            output = "arcanis"
        } else if (command === "uname") {
            output = "ARCANIS OS v14.0.0 (build 2026) Windows x64"
        } else if (command === "exit") {
            var p = root.parent
            while (p) {
                if (p.closeRequested !== undefined) {
                    p.closeRequested()
                    return
                }
                p = p.parent
            }
            return
        } else if (command === "ls") {
            output = "Desktop/\nDocuments/\nDownloads/\nMusic/\nPictures/\nVideos/\narc/"
        } else {
            output = "Command not found: " + command + "\nType 'help' for available commands"
        }

        Qt.createQmlObject(
            'import QtQuick; Column { ' +
            '  Text { text: "' + root.prompt.replace(/"/g, '\\"') + cmd.replace(/"/g, '\\"') + '"; color: "#0066cc"; font.pixelSize: 11; font.family: "Consolas" } ' +
            '  Text { text: "' + output.replace(/"/g, '\\"').replace(/\n/g, '\\n') + '"; color: "#1a1a1a"; font.pixelSize: 11; font.family: "Consolas" } ' +
            '}',
            outputArea, "termOutput"
        )
    }
}
