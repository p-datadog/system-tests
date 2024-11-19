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

  # Padding
  # Padding
  # Padding
  # Padding

  def pii
    pii = Pii.new
    customPii = CustomPii.new
    render inline: 'pii' # This needs to be line 31
  end
end
