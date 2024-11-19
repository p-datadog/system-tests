class BasePii
  def initialize
    @custom_value = 'should be redacted'
  end
  
  attr_reader :custom_value
end
