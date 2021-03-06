# Dolphin-Updater
Update to the newest version of Dolphin Emulator with a click of a button!
<br />
### Release 3.0 Features:
* Detect newest version and download
* Launch dolphin directly from the app
* Shows a recent changelog
* Option to auto-launch dolphin
* Command line capabilities
* Compatible with dev builds from Dolphin 5.0 and up!

After setting up, select which folder you keep dolphin in using the folder button, then click the download button to install the newest version. **Administrator is only required if your dolphin path is a system protected folder.**

Here's what the application will look like:

![app_example](https://user-images.githubusercontent.com/18427811/31310946-eae05954-ab6f-11e7-8b5f-7a803c09c0b2.PNG)

Command Line Usage Example:
<pre><code>"C:\Program Files (x86)\DolphinUpdate\DolphinCmd" --help     (list all command line arguments)
"C:\Program Files (x86)\DolphinUpdate\DolphinCmd" -d         (download the newest version)
</code></pre>

You can also do something like this:
<pre><code>cd C:\Program Files (x86)\DolphinUpdate     (change active directory)
DolphinCmd -i                               (provide information about your installation)
</code></pre>

This should also allow you to update dolphin with Windows Task Scheduler.

**Just make sure you add the app folder to scheduler's "Start In" parameter or downloading will fail<br/> eg: <code> Start In (optional): C:\Program Files(x86)\DolphinUpdate</code>**

<br />
<br />
Dolphin website:
https://dolphin-emu.org/

7zip is now packaged with this program:
http://www.7-zip.org/

Source code has been compiled using PyInstaller and InnoSetup 5 (bat file is provided to compile easily)
