class KeyPressedNotifier():
    event_handlers = []

    @staticmethod
    def subscribe(handler):
        try:
            KeyPressedNotifier.event_handlers.append(handler)
        except Exception as e:
            print("Error during event subscription: " + str(e))
        

    @staticmethod
    def notify(key):
        try:
            for handler in KeyPressedNotifier.event_handlers:
                handler(key)
        except Exception as e:
            print("Error during event notification: " + str(e))