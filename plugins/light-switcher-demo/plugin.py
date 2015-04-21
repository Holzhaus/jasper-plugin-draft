from core.plugin.types import SpeechHandlerPlugin


class LightSwitcherDemo(SpeechHandlerPlugin):
    def configure(self):
        self.register_option('location1-name', default_value="livingroom")
        self.register_option('location2-name', default_value="bedroom")
        self.register_option('location3-name', default_value="kitchen")
        self.register_option('location4-name', default_value="bathroom")
        self.register_option('location1-enabled', default_value=True,
                             is_boolean=True)
        self.register_option('location2-enabled', default_value=True,
                             is_boolean=True)
        self.register_option('location3-enabled', default_value=True,
                             is_boolean=True)
        self.register_option('location4-enabled', default_value=True,
                             is_boolean=True)

    @property
    def locations(self):
        locations = {}
        for i in range(1, 5):
            if self.get_option('location%d-enabled' % i):
                location_name = self.get_option('location%d-name' % i)
                if location_name:
                    locations[location_name] = i
        return locations

    def activate(self):
        locations = self.locations.keys()
        if locations:
            self.register_command("switch {location} lights {state}",
                                  self.switch_lights,
                                  location=locations,
                                  state=['on', 'off'])

    def switch_lights(self, conversation, location='', state=''):
        # FIXME: For demonstration purposes only
        conversation.say(("switch_lights command called for location '%s' " +
                         "and state '%s'") % (location, state))
