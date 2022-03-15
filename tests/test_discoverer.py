import signal


# content on_usr1_signal function test
def test_on_usr1_signal(discoverer):
    # In case scanning is still in progress
    assert discoverer.signal_received == False
    assert discoverer.on_usr1_signal(signal.SIGUSR1) == None
    # Otherwise
    discoverer.numdirs = 0
    usr1 = discoverer.on_usr1_signal(signal.SIGUSR1)
    assert discoverer.signal_received == True
    assert usr1 == True
    discoverer.numdirs = 0
    discoverer.signal_received = False
    usr2 = discoverer.on_usr1_signal(signal.SIGUSR2)
    assert discoverer.signal_received == False
    assert usr2 == None
