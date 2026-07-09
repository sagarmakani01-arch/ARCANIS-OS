import pytest
from arcanis_inference.engine import InferenceEngine
from arcanis_inference.config import InferenceConfig
from arcanis_inference.backends.dummy import DummyBackend
from arcanis_inference.models.intent import IntentClassifier


class TestInferenceEngine:
    def setup_method(self):
        self.config = InferenceConfig()
        self.engine = InferenceEngine(self.config)
        self.engine.initialize(backend=DummyBackend())

    def teardown_method(self):
        self.engine.shutdown()

    def test_initialization(self):
        status = self.engine.get_status()
        assert status["initialized"] is True
        assert status["model_loaded"] is False

    def test_classify_intent(self):
        result = self.engine.classify_intent("create a new file called test.py")
        assert result["intent"] == "file_operation"
        assert result["confidence"] > 0.0

    def test_classify_process(self):
        result = self.engine.classify_intent("kill process 1234")
        assert result["intent"] == "process_management"

    def test_classify_code(self):
        result = self.engine.classify_intent("write a function to sort an array")
        assert result["intent"] == "code_generation"

    def test_classify_question(self):
        result = self.engine.classify_intent("what is the current directory")
        assert result["intent"] in ["question_answering", "system_info"]

    def test_shutdown(self):
        self.engine.shutdown()
        status = self.engine.get_status()
        assert status["initialized"] is False


class TestIntentClassifier:
    def setup_method(self):
        self.config = InferenceConfig()
        self.classifier = IntentClassifier(self.config)

    def test_file_operations(self):
        intents = [
            ("create a file named test.txt", "file_operation"),
            ("delete the old backup", "file_operation"),
            ("list all files in the directory", "file_operation"),
            ("find files matching *.py", "file_operation"),
        ]
        for text, expected in intents:
            intent, confidence = self.classifier.classify(text)
            assert intent == expected, f"Failed for '{text}': got {intent}"

    def test_process_management(self):
        intents = [
            ("run the compiler", "process_management"),
            ("kill process 42", "process_management"),
            ("list running processes", "process_management"),
        ]
        for text, expected in intents:
            intent, confidence = self.classifier.classify(text)
            assert intent == expected, f"Failed for '{text}': got {intent}"

    def test_general_fallback(self):
        intent, confidence = self.classifier.classify("hello world")
        assert intent == "general"

    def test_supported_intents(self):
        intents = self.classifier.get_supported_intents()
        assert "file_operation" in intents
        assert "general" in intents
        assert len(intents) >= 8
