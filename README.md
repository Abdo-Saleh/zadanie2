# Communication using UDP protocol.


[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

# Application Features:
  - choose mode (server or client)
  - set IP for the destenation (client mode)
  - set port for the destenation (client mode)
  - set fragment size (client mode)
  - send text smaller than the fragment size
  - send text bigger than the fragment size
  - simulate error of a trasfered packet (small file)
  - logging the fragments states
  - keep alive
  - ARQ stop-wait
  - Server check the coorection of the sent fragment    
        - Ask again for the same fragment in case error-detection
  - CRC 16 bit (check sum)
 
### How to run
 - run the script two times and enjoy