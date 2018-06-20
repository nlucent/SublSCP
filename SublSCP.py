# Loosely based on https://gist.github.com/jijojv/8139217
# Nick Lucent

import sublime, sublime_plugin, os

class SublScpCommand(sublime_plugin.TextCommand):

    hosts = []
    paths = {}
    preferredhost = None

    def run(self, edit):
        s = sublime.load_settings("SublSCP.sublime-settings")
        self.hosts = s.get("hosts")
        self.paths = s.get("paths")

        if s.has("preferredhost"):
            self.preferredhost = s.get("preferredhost")
        else:
            self.preferredhost = None

        for dirname, target in self.paths.items():
            if self.view.file_name().startswith(dirname):
                if not self.preferredhost:
                    self.view.window().show_quick_panel(self.hosts, self.on_done)
                else:
                    self.docopy(self.preferredhost)
    def on_done(self, index):
        if index == -1:
            return

        self.docopy(self.hosts[index])
    def docopy(self, host):
        scp = ScpFile()

        for dirname, target in self.paths.items():
            if self.view.file_name().startswith(dirname):
                val = scp.do_work(self.view, dirname, host, target)
                if val == 0:
                    print("SUCCESS! - ", dirname, host, target)
                    sublime.status_message("SUCCESS!: " + host)
                else:
                    print(val)
                    sublime.error_message("Error")

class SublScpAllCommand(sublime_plugin.WindowCommand):

    hosts = []
    files = 0
    copied = 0
    preferredhost = None

    def run(self):
        s = sublime.load_settings("SublSCP.sublime-settings")
        if s.has("preferredhost"):
            self.preferredhost = s.get("preferredhost")
        else:
            self.preferredhost = None
        self.hosts = s.get("hosts")
        self.paths = s.get("paths")
        if not self.preferredhost:
            self.window.show_quick_panel(self.hosts, self.on_done)
        else:
            self.docopy(self.preferredhost)
    def on_done(self, index):
        if index == -1:
            return
        self.docopy(self.hosts[index])
    def docopy(self, host):
        scp = ScpFile()

        for v in self.window.views_in_group(self.window.active_group()):
            for dirname, target in self.paths.items():
                if v.file_name() is not None and v.file_name().startswith(dirname):
                    self.files += 1
                    if scp.do_work(v, dirname, host, target) == 0:
                        self.copied += 1
                        print("SUCCESS - ", dirname, host, target)

        if self.copied == self.files:
            statusstr =  "Copied " + str(self.files) + " / " + str(self.copied)
            sublime.status_message("SUCCESS! - " + statusstr + " " + host)
            self.files = 0
            self.copied = 0

class SetScpHostCommand(sublime_plugin.TextCommand):
    hosts = []
    settings = None

    def run(self, edit):
        self.settings = sublime.load_settings("SublSCP.sublime-settings")
        self.hosts = self.settings.get("hosts")
        self.hosts.insert(0,"Unset")

        self.view.window().show_quick_panel(self.hosts, self.on_done)

    def on_done(self, index):
        if index == -1:
            return

        if index == 0:
            self.settings.erase("preferredhost")
            sublime.save_settings("SublSCP.sublime-settings")
        else:
            self.settings.set("preferredhost", self.hosts[index])
            sublime.save_settings("SublSCP.sublime-settings")

class AddScpHostCommand(sublime_plugin.WindowCommand):
    hosts = []
    settings = None
    def run(self):
        self.settings = sublime.load_settings("SublSCP.sublime-settings")
        self.hosts = self.settings.get("hosts")
        self.window.show_input_panel("Add SCP Host", "user@host", self.on_done, None, None)

    def on_done(self, newhost):
        self.hosts.append(newhost)
        self.settings.set("hosts", self.hosts)
        sublie.save_settings()

class ScpFile:
    scpbin = None
    paths = {}

    def do_work(self, view, localpath, target, remotepath):
        s = sublime.load_settings("SublSCP.sublime-settings")
        self.scpbin = s.get("scp")

        src = view.file_name()
        dest = str(remotepath) + str(src[len(localpath):])
        destdir = os.path.dirname(dest)
        cmd = tuple([self.scpbin, src, target, dest] )
        if os.system("ssh %s 'mkdir -p %s'" % (target, destdir)) == 0:
            return os.system("%s %s %s:%s" % cmd)
        return {"target":target,"destdir":destdir}
