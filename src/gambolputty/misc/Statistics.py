import time
import Utils
import BaseModule
import Decorators

@Decorators.ModuleDocstringParser
class Statistics(BaseModule.BaseModule):
    """
    Collect and log some statistic data.

    Configuration example:

    - module: Statistics
      configuration:
        print_interval: 10                 # <default: 10; type: integer; is: optional>
        event_type_statistics: True        # <default: True; type: boolean; is: optional>
        receive_rate_statistics: True      # <default: True; type: boolean; is: optional>
        waiting_event_statistics: True     # <default: True; type: boolean; is: optional>
    """

    module_type = "misc"
    """Set module type"""

    def configure(self, configuration):
        # Call parent configure method
        BaseModule.BaseModule.configure(self, configuration)
        self.stats_collector.setCounter('ts_last_stats', time.time())
        self.printTimedIntervalStatistics()
        self.module_queues = {}

    @Decorators.setInterval(10)
    def printTimedIntervalStatistics(self):
        self.logger.info("############# Statistics #############")
        if self.getConfigurationValue('receive_rate_statistics'):
            self.receiveRateStatistics()
        if self.getConfigurationValue('waiting_event_statistics'):
            self.eventsInQueuesStatistics()
        if self.getConfigurationValue('event_type_statistics'):
            self.regexStatistics()

    def regexStatistics(self):
        self.logger.info(">> EventTypes Statistics")
        for event_type, count in sorted(self.stats_collector.getAllCounters().iteritems()):
            if not event_type.startswith('event_type_'):
                continue
            self.logger.info("EventType: %s%s%s - Hits: %s%s%s" % (Utils.AnsiColors.YELLOW, event_type.replace('event_type_', ''), Utils.AnsiColors.ENDC, Utils.AnsiColors.YELLOW, count, Utils.AnsiColors.ENDC))
            self.stats_collector.resetCounter(event_type)

    def receiveRateStatistics(self):
        self.logger.info(">> Receive rate stats")
        eps = self.stats_collector.getCounter('eps')
        if not eps:
            eps = 0
        self.stats_collector.resetCounter('eps')
        self.logger.info("Received events in %ss: %s%s (%s/eps)%s" % (self.getConfigurationValue('print_interval'), Utils.AnsiColors.YELLOW, eps, (eps/self.getConfigurationValue('print_interval')), Utils.AnsiColors.ENDC))

    def eventsInQueuesStatistics(self):
        if len(self.module_queues) == 0:
            return
        self.logger.info(">> Queue stats")
        for module_name, queue in self.module_queues.iteritems():
            self.logger.info("Events in %s queue: %s%s%s" % (module_name, Utils.AnsiColors.YELLOW, queue.qsize(), Utils.AnsiColors.ENDC))

    def run(self):
        # Get all configured queues for waiting event stats.
        for module_name, module_info in self.gp.modules.iteritems():
            instance = module_info['instances'][0]
            if not hasattr(instance, 'getInputQueue') or not instance.getInputQueue():
                continue
            self.module_queues[module_name] = instance.getInputQueue()

    def destroyEvent(self, event=False, event_list=False):
        """Statistic module will not destroy any events."""
        pass

    def handleEvent(self, event):
        self.stats_collector.incrementCounter('eps')
        if self.getConfigurationValue('event_type_statistics'):
            try:
                self.stats_collector.incrementCounter('event_type_%s' % event['event_type'])
            except:
                pass
        yield event
