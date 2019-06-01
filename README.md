# numenworld-ipcam
Out of morbid curiousity I bought the cheapest IP camera that I could find. For
me this was on AliExpress the "NuMenWorld I536A", sold for about 18€ with S&H
included and sold as a "2.0MP network IP cam 1080P HD Built-in microphone CCTV
Video surveillance dome security IP camera ONVIF day/night indoor webcams". It
seems to support ONVIF and, allegedly, has a full HD sensor capable of
producing 1080p. The official website that is listed on the camera is
[http://www.XMeye.net](www.XMeye.net). On the stricker it says "Product Name:
NCV-I536A Audio", specifies a length of 3.6mm (I'm guessing focal length of the
lens?), it also says H.265+ and that it takes 12V DC power at 2A. My camera was
produced in May of 2019. This project documents my playing around with this
camera and documentation of my findings and reverse engineering efforts.

## Communication
The camera boots up with the static default IP address of 192.168.1.10 and a
username of "admin" and empty password. It has multiple open ports:

```
Starting Nmap 7.60 ( https://nmap.org ) at 2019-06-01 16:48 CEST
Nmap scan report for crappywebcam.homelan.net (192.168.1.10)
Host is up (0.0053s latency).
Not shown: 65529 closed ports
PORT      STATE SERVICE
80/tcp    open  http
554/tcp   open  rtsp
8000/tcp  open  http-alt
8899/tcp  open  ospf-lite
9530/tcp  open  unknown
34567/tcp open  dhanalakshmi

Nmap done: 1 IP address (1 host up) scanned in 5.50 seconds
```

On port 80, a webserver listens that has its webinterface in Chinese. This can
only be changed using the included supercrappy software, not from the
webinterface itself. In any case, you're greeted with the first LOL moment of
this camera, where it informs you that you should really use an older browser:

![Camera demands old browser](/doc/img/old-webbrowsers-rule.png)

So a 2019 Chromium is too new and the camera would much prefer if I used a four
year old version from 2015. Cool.

Anyways, upon clicking the login button, curiously nothing happens at first.
Then it does. Hmm. Why? This seems odd. Well, we can easily find out when we
follow the code (formatting done by me, it's a oneliner in the original):

```javascript
var now = new Date(); 
var exitTime = now.getTime() + 2000; 
while (true) { 
	now = new Date(); 
	if (now.getTime() > exitTime) {	
		break;
	}
} 
```

You *have* to be kidding me. A random two second delay to make the login
process seem more "substantial", I guess? Or maybe the "top of the line" model
doesn't have that stupid delay because it is more "powerful"? What piece of
crap is this? This kind of ridiculous development practice is completely
unacceptable.

Anyways, the other port that I saw used was 34567, using a binary/JSON mixed
protocol to get/set many properties. It actually allows pretty fine-grained
control over the chip, which I find pretty cool. Very low-level access is
possible to parameters like exposure and night vision cutoff. That protocol is
what I took a look at in the provided code as well.

On the RTSP port I was so far unable to get a RTSP data stream. Not sure how it
works, still poking around a bit.

No idea what runs on ports 8000 or 9530. But another web server seems to run on
port 8899 that seems to expect SOAP.

## Security
Early on in the reverse engineering, it's clear that both on the web interface
and the internal protocol on port 34567 do not transmit the passwords in plain
text. Unfortunately, what they do use is only slightly crappier. Here's how it
works: They take the MD5 of the passphrase, this gives 16 bytes as a result.
Sum every second byte so you get 8 resulting values. Then take those modulo 62
and look up from the alphabet string
"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz". In other
words:

```python
md5 = hashlib.md5(passphrase).digest()
alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
passphrase = alphabet[(md5[0] + md5[1]) % 62]
	+ alphabet[(md5[1] + md5[2]) % 62]
	+ alphabet[(md5[3] + md5[4]) % 62]
	...
	+ alphabet[(md5[14] + md5[15]) % 62]
```

Actual working code can be found in HorrificallyBrokenPasswordFunction.py.

## License
All of my code is GPL-3.
