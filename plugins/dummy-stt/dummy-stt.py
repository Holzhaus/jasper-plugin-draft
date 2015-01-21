from core.plugintypes import STTPlugin


class DummySTT(STTPlugin):

    def configure(self):
        self.register_option('some-config-key', default_value='some value')

    def transcribe(self, audio_file_path, PERSONA_ONLY=False, MUSIC=False):
        return ""

    def get_languages():
        # TODO: return a list of languages
        return ["en_US"]
