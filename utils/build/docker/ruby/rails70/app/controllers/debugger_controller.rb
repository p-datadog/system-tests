# Padding
# Padding
# Padding
# Padding

class DebuggerController < ActionController::Base
  def init
    # This method does nothing.
    # When the endpoint corresponding to it is invoked however,
    # the middleware installed by dd-trace-rb initializes remote configuration.
    render inline: 'debugger init'
  end
  
  def pii
    puts '---- DEBUGGER PII----'
    render inline: 'pii'
  end
  
  def log_probe
    render inline: 'Log probe' # This needs to be line 20
  end
end
