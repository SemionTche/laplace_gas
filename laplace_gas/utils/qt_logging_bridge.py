"""
Qt logging bridge.
Emits a Qt signal for every logging record.
"""

# import logging
# from PyQt6.QtCore import QObject, pyqtSignal


# class QtLogEmitter(QObject):
#     log_received = pyqtSignal(str)


# class QtLogHandler(logging.Handler):
#     """
#     Logging handler that forwards formatted log records to a Qt signal.
#     """

#     def __init__(self, emitter: QtLogEmitter):
#         super().__init__()
#         self.emitter = emitter
    
#         self.setFormatter(logging.Formatter(
#             "[%(levelname)s] %(message)s"
#         ))

#     def emit(self, record: logging.LogRecord):
#         try:
#             msg = self.format(record)
#             self.emitter.log_received.emit(msg)
#         except Exception:
#             pass


import logging
from PyQt6 import QtCore

class QtLogHandler(logging.Handler, QtCore.QObject):
    """Logging handler that emits log messages as Qt signals."""
    new_log = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)
        
        # Set formatter directly here
        self.setFormatter(logging.Formatter("[%(levelname)s] [%(name)s] %(message)s"))

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)  # applies formatter automatically
        self.new_log.emit(msg)
