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

  # Padding
  # Padding
  # Padding
  # Padding

  def log_probe
    render inline: 'Log probe' # This needs to be line 20
  end

  def pii
    puts '---- DEBUGGER PII----'
    var = 1
    render inline: 'pii' # This needs to be line 26
  end
end
