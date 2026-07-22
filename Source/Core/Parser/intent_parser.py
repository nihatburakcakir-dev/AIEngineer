class IntentParser:

    def __init__(self):

        self.intent_map = {

            "create":"CREATE_OBJECT",
            "generate":"GENERATE_CONTENT",
            "spawn":"CREATE_OBJECT",
            "new":"CREATE_OBJECT",

            "delete":"DELETE_OBJECT",
            "remove":"DELETE_OBJECT",
            "destroy":"DELETE_OBJECT",
            "sil":"DELETE_OBJECT",

            "modify":"MODIFY_OBJECT",
            "change":"MODIFY_OBJECT",
            "edit":"MODIFY_OBJECT",
            "değiştir":"MODIFY_OBJECT",
            "duzenle":"MODIFY_OBJECT",
            "düzenle":"MODIFY_OBJECT",

            "move":"MOVE_OBJECT",
            "taşı":"MOVE_OBJECT",

            "rotate":"ROTATE_OBJECT",
            "döndür":"ROTATE_OBJECT",

            "scale":"SCALE_OBJECT",
            "resize":"SCALE_OBJECT",
            "büyüt":"SCALE_OBJECT",
            "küçült":"SCALE_OBJECT",

            "color":"CHANGE_COLOR",
            "renk":"CHANGE_COLOR",
            "kırmızı":"CHANGE_COLOR",
            "mavi":"CHANGE_COLOR",
            "yeşil":"CHANGE_COLOR",
            "sarı":"CHANGE_COLOR",
            "beyaz":"CHANGE_COLOR",
            "siyah":"CHANGE_COLOR",

            "sprite":"GENERATE_SPRITE",
            "prefab":"CREATE_PREFAB",
            "scene":"CREATE_SCENE",
            "script":"CREATE_SCRIPT",
            "refactor":"REFACTOR",
            "yeniden adlandır":"REFACTOR",
            "performans":"ANALYZE_PERFORMANCE",
            "performance":"ANALYZE_PERFORMANCE",
            "bug":"DETECT_BUG",
            "hata":"DETECT_BUG",
            "ölü kod":"DETECT_DEAD_CODE",
            "dead code":"DETECT_DEAD_CODE"
        }

        self.increase_words = {
            "artır",
            "arttir",
            "arttır",
            "increase",
            "boost",
            "yükselt",
            "hızlandır",
            "çoğalt"
        }

        self.decrease_words = {
            "azalt",
            "decrease",
            "reduce",
            "düşür",
            "yavaşlat"
        }

    def parse(self, text):

        text = text.lower()

        engineering_intents = (
            (("refactor", "yeniden adlandır"), "REFACTOR"),
            (("performans", "performance"), "ANALYZE_PERFORMANCE"),
            (("bug", "hata"), "DETECT_BUG"),
            (("ölü kod", "dead code"), "DETECT_DEAD_CODE"),
        )

        for keywords, intent in engineering_intents:
            if any(keyword in text for keyword in keywords):
                return intent

        if any(w in text for w in self.increase_words):
            return "MODIFY_FIELD"

        if any(w in text for w in self.decrease_words):
            return "MODIFY_FIELD"

        for key, value in self.intent_map.items():

            if key in text:
                return value

        return "UNKNOWN"
