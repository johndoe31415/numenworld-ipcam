# numenworld-ipcam
Out of morbid curiousity I bought the cheapest IP camera that I could find. For
me this was on AliExpress the "NuMenWorld I536A", sold for about 18€ with S&H
included and sold as a "2.0MP network IP cam 1080P HD Built-in microphone CCTV
Video surveillance dome security IP camera ONVIF day/night indoor webcams". It
seems to support ONVIF and, allegedly, has a full HD sensor capable of
producing 1080p. The official website that is listed on the camera is
[www.XMeye.net](http://www.XMeye.net). On the stricker it says "Product Name:
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

## Cloud Communication
The camera is, by default, trying to connect to some kind of cloud service. It
sends various UDP telegrams and TCP connections out. I am *very* suspicious of
this communication and think there's a very good possibility that a specific
reply to one of these datagrams enables either remote firmware download or
complete remote control (i.e., using TCP for NAT traversal). It is my
professional opinion as a security researcher that I *strongly* advise to block
all of this activity in your firewall, via effective means (e.g., VLAN jailing
and filtering since we cannot assume the device will reliably use its assigned
MAC or IP address).

In any case, the camera uses two public DNS servers that are entirely
independent of your local setup, 114.114.114.114 (AKA public1.114dns.com, a
Chinese DNS provider) and 8.8.8.8 (AKA google-public-dns-a.google.com, Google's
public DNS).

It then resolves pub-cfg.secu100.net and mac.secu100.net. Fun fact: The DNS
response that the Chinese webserver gives is a different IP than the one that Western
ones give:

```
$ host mac.secu100.net
mac.secu100.net has address 35.158.174.16
$ host 35.158.174.16
16.174.158.35.in-addr.arpa domain name pointer ec2-35-158-174-16.eu-central-1.compute.amazonaws.com.


$ host mac.secu100.net 8.8.8.8
Using domain server:
Name: 8.8.8.8
Address: 8.8.8.8#53
Aliases: 

mac.secu100.net has address 35.158.174.16

$ host mac.secu100.net 114.114.114.114
Using domain server:
Name: 114.114.114.114
Address: 114.114.114.114#53
Aliases: 

mac.secu100.net has address 54.254.159.106
$ host 54.254.159.106
106.159.254.54.in-addr.arpa domain name pointer ec2-54-254-159-106.ap-southeast-1.compute.amazonaws.com.
```

I.e., it seems to connect to an APAC AWS instance instead of a European one.
The most benign reason for this would be automatic geolocation to determine the
fastest server in proximity of the resolver, but more malicious explanations
are thinkable as well and are left up to the reader.

After DNS resolution, it does a TCP connect to the first domain
(pub-cfg.secu100.net) on port 8086 and performs a HTTP POST request (message
body and response body was formatted by me for better readability):

```
POST / HTTP/1.1
CSeq: 1
Host: 54.193.123.32
Content-Length: 303

{
    "CfgProtocol": {
        "Body": {
            "AuthCode": "REDACTED",
            "OemID": "General",
            "OtherInfo": "V5.00.R02.00030678.10010.246701.00200",
            "ProductID": "XM530_80X20_8M",
            "SerialNumber": "REDACTED"
        },
        "Header": {
            "CSeq": "1",
            "MessageType": "MSG_DSS_CFG_QUERY_REQ",
            "Version": "1.0"
        }
    }
}
HTTP/1.1 200 OK
Server: openresty/1.9.3.1
Date: Sat, 01 Jun 2019 14:23:32 GMT
Content-Type: text/html
Connection: keep-alive
content-length: 338

{
    "CfgProtocol": {
        "Body": {
            "Area": "Europe:Germany:Default",
            "AuthCodeReTry": "1800",
            "ErrReTry": "60",
            "MainStreamEnable": "1",
            "MainStreamMaxFps": "6",
            "RewriteOemDomainName": "52.58.71.125",
            "SnapInterval": "3",
            "SnapPicture": "1"
        },
        "Header": {
            "CSeq": "1",
            "ErrorNum": "200",
            "ErrorString": "Success OK",
            "MessageType": "MSG_DSS_CFG_QUERY_RSP",
            "Version": "1.0"
        }
    }
}
```

Interestingly, the "AuthCode" and "SerialNumber" are indeed the indentical 8
bytes (Base16 formatted). It also appears as if the cloud communication could
remotely tell the camera to only support a maximum frame rate. Possibly it can
therefore be remotely "unlocked" at giving a greater framerate by simply
impersonating that configuration webserver. Since it doesn't use any kind of
security/authentication, this should be exceptionally easy to try.

Then it connects to the second server and transmits this:

```
POST / HTTP/1.1
Host:access-dss.secu100.net
Connection: keep-alive
Content-Length:361

{
    "DssProtocol": {
        "Body": {
            "Area": "Europe:Germany:Default",
            "AuthCode": "REDACTED",
            "LiveStatus": [
                "0",
                "0"
            ],
            "RewriteOemID": "General",
            "SerialNumber": "REDACTED",
            "StreamLevel": "0_3:1_1_0",
            "StreamServerIPs": [
                "0.0.0.0",
                "0.0.0.0"
            ]
        },
        "Header": {
            "CSeq": "1",
            "MessageType": "MSG_DEV_REGISTER_REQ",
            "Version": "1.0"
        }
    }
}
HTTP/1.1 200 OK
Content-Length: 287
Content-Type: text/plain

{
   "DssProtocol" : {
      "Body" : {
         "KeepAliveIntervel" : "120"
      },
      "Header" : {
         "CSeq" : "1",
         "ErrorNum" : "200",
         "ErrorString" : "Success OK",
         "MessageType" : "MSG_DEV_REGISTER_RSP",
         "Version" : "1.0"
      }
   }
}
```

I.e., this seems to be some kind of cloud registry -- DSS could stand for
Direct/Digital Streaming Service or something along the lines.

Then there's two more TCP streams exchanged:

```
POST / HTTP/1.1
CSeq: 1
Host: 54.193.123.32
Content-Length: 330

{
    "CfgProtocol": {
        "Body": {
            "AuthCode": "REDACTED",
            "OemID": "General",
            "OtherInfo": "V5.00.R02.00030678.10010.246701.00200",
            "ProductID": "XM530_80X20_8M",
            "SerialNumber": "REDACTED"
        },
        "Header": {
            "CSeq": "1",
            "MessageType": "MSG_PMS_CFG_QUERY_REQ",
            "TerminalType": "Camera",
            "Version": "1.0"
        }
    }
}
HTTP/1.1 200 OK
Server: openresty/1.9.3.1
Date: Sat, 01 Jun 2019 14:23:34 GMT
Content-Type: text/html
Connection: keep-alive
content-length: 595

{
    "CfgProtocol": {
        "Body": {
            "Area": "Europe:Germany:Default",
            "AuthCodeReTry": "1800",
            "ErrReTry": "60",
            "PushInterval": "10",
            "PushMsg": "LocalAlarm|MotionDetect|LossDetect|ConsSensorAlarm|BlindDetect|IPCAlarm|LocalIO|StorageWriteError|StorageFailure|StorageLowSpace|StorageNotExist|SerialAlarm|VideoAnalyze|ConsSensorAlarm|HumanDetect|PIRAlarm",
            "PushPicture": "0",
            "RewriteOemDomainName": "52.58.71.125",
            "RewriteOemDomainNamePicture": "159.138.23.80",
            "SnapInterval": "3",
            "SnapPicture": "0"
        },
        "Header": {
            "CSeq": "1",
            "ErrorNum": "200",
            "ErrorString": "Success OK",
            "MessageType": "MSG_PMS_CFG_QUERY_RSP",
            "Version": "1.0"
        }
    }
}
```

And finally:

```
POST /dev/upload HTTP/1.1
Host: caps.xmcsrv.net
Content-Length: 767

{
    "CapsCenter": {
        "Body": {
            "BuildTime": "2019-03-27 15:04:59",
            "DevInfo": {
                "CRC": 378,
                "Data": "sruL3QR/r375nUOuC1WcsA==",
                "DeviceType": 0,
                "EncrptType": "ExAbility",
                "Key": "78997780"
            },
            "EncryptChipInfo": {
                "Base": 0,
                "DssLevel": 0,
                "EnBase": 0,
                "ExtraLevel": 0,
                "Intel": 0,
                "IntelCPC": 0,
                "IpcDeviceType": 0,
                "Nat": 1,
                "OEMID": 0,
                "OEMProuct": 0,
                "OEMSerial": 0,
                "Resolution": 0,
                "Version": "V1.0"
            },
            "HardWare": "XM530_80X20_8M",
            "MacAddr": "RE:DA:CT:ED:XX",
            "MfrsInfo": null,
            "NewVersionSN": "REDACTED",
            "OldVersionSN": "REDACTED",
            "SerialNumber": "REDACTED",
            "SoftExAbilityMask": 0,
            "SoftWare": "V5.00.R02.00030678.10010.246701.00200"
        },
        "Header": {
            "MessageType": "REPORT_CAPS_DEV_INFO_REQ"
        }
    }
}
HTTP/1.1 200 
Server: nginx/1.12.2
Date: Sat, 01 Jun 2019 14:23:35 GMT
Content-Type: application/json;charset=UTF-8
Transfer-Encoding: chunked
Connection: keep-alive
X-Application-Context: application:production

d9
{
    "CapsCenter": {
        "Body": {
            "CRC": 378,
            "Data": "sruL3QR/r375nUOuC1WcsA==",
            "DeviceType": 0,
            "EncrptType": "ExAbility",
            "Key": "78997780"
        },
        "Header": {
            "ErrorNum": 200,
            "ErrorString": "Success",
            "MessageType": "REPORT_CAPS_DEV_INFO_RSP"
        }
    }
}
0
```

Very curious. Especially the CRC-protected encrypted (?) data that it exchanges
with the servers is a bit odd. If we can trust the metadata it just is
reporting its capabilties to the server, which could well be true.

In any case there's also numerous UDP datagrams that are sent which use a
proprietary binary protocol. Transmitted information seems also to be the
serial number, various IP addresses and the MAC address of the camera itself.

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
