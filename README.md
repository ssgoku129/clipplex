> #### **_I don't know if this needs to be said or not but Please do not use this tool with public access, I did not create this but I would not trust this with access to my Plex Media Server exposed to the internet, YOU HAVE BEEN WARNED!_**

# Clipplex

A friend of mine stumbled across this [project](https://github.com/jo-nike/clipplex) and asked if I could make it compatible for his Windows Plex server which has a single hard drive attached with all their media so I added some simple commands to translate the Windows Path to linux, accompany this conmtainerized tool with [WinNFSd](https://github.com/winnfsd/winnfsd) and version 3 while mounting, you can share your external plex server and drive with your clipplex from a Windows desktop OS over NFS!

## Description

Have you ever, while watching something on your plex server, wanted to easily extract a clip out of a good movie or tv show you're watching to share it with your friend, family or the world? While this was always possible, the process can be complex for something "so simple".

![](https://github.com/ssgoku129/clipplex/blob/master/example.gif)

In this fork, I simply added a translator for the Windows paths so they are compatible with Linux, using a combination of WinNFSd and a simple batch script on startup called nfs_share.bat for example, containing the following:

```.\WinNFSd.exe "L:/" /l```

This will share the external drive L: as an NFS path [WIN_PLEX_IP]:/l/

Then I simply add the following config to the docker script:

 ``` -v /WIN_PLEX_IP/:/l \```

And now we have the path mounted perfctly for clipplex to translate, enjoy clipping on your Windows servers!

## Docker variables

| Variables            | Value            | Notes     |
| ---------------------|:----------------:| ----------|
| PUID                 | 1000             | Optional  |
| GUID                 | 1000             | Optional  |
| TZ                   | America/Toronto  | Optional  |
| PLEX_URL             | link to plex     | Mandatory |
| PLEX_TOKEN           | token for plex   | Mandatory |
| STREAMABLE_LOGIN     | ...              | Optional  |
| STREAMABLE_PASSWORD  | ...              | Optional  |

Finding Plex token: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

Volumes: You will need to mount two locations:
* one that point to your media, in the exact same fashion your plex access these media (as the path are absolutes) 
* one where the new clips will be created.

media need to be mounted into the container path: /media when using Linux

media needs to be mounted exactly how the Windows path is, i.e. 'L:\TV Shows' = '/l/TV\ Shows'

clips need to be mounted into the container path: /app/app/static/media (yes, I'll get that better eventually).

Port: Port 5000 is used to serve the frontend. (yes I will serve flask with gunicorn at some point)

Network: Need to be on the same network as your plex instance.

```
docker run -d --name clipplex -p 9945:5000 -v /media:/media -v /volumes/clipplex:/app/app/static/media --restart always -e PUID=1000 -e PGID=1000 -e TZ=America/Toronto -e PLEX_URL=YOURPLEXURL -e PLEX_TOKEN=YOURPLEXTOKEN jonnike/clipplex:latest
```

## Docker Compose Example
```
version: "3.5"
networks:
  docker_internal_network:
    name: plex_stack
  clipplex:
    image: jonnike/clipplex:latest
    container_name: clipplex-alpha
    networks:
      - docker_internal_network
    environment:
      - PYTHONUNBUFFERED=1
      - PUID=1000
      - PGID=1000
      - TZ=America/New_York
      - PLEX_URL=YOUR_PLEX_URL (example: http://plex:32400)
      - PLEX_TOKEN=YOUR_PLEX_TOKEN
      - STREAMABLE_LOGIN=YOUR_STREAMABLE_LOGIN
      - STREAMABLE_PASSWORD=YOUR_STREAMABLE_PASSWORD
    volumes:
      - /media:/media
      - /volumes/clipplex:/app/app/static/media
    ports:
      - 9945:5000
```

## Authors

ssgoku129 - expanded for use with Windows

Jo Nike - Original contributor

## Version History
* 0.0.9
    Made the path conversion deal with special characters a little better

* 0.0.8
    Added Path conversions for Windows Servers

* 0.0.3
    
    Initial Release

## License

Distributed under the MIT License. See the LICENSE file information.
