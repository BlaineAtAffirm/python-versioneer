
import sys
import re
import os.path

def get_expanded_variables(versionfile_source):
    # the code embedded in _version.py can just fetch the value of these
    # variables. When used from setup.py, we don't want to import
    # _version.py, so we do it with a regexp instead. This function is not
    # used from _version.py.
    variables = {}
    try:
        for line in open(versionfile_source,"r").readlines():
            if line.strip().startswith("git_refnames ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    variables["refnames"] = mo.group(1)
            if line.strip().startswith("git_full ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    variables["full"] = mo.group(1)
    except EnvironmentError:
        pass
    return variables

def versions_from_expanded_variables(variables, tag_prefix):
    refnames = variables["refnames"].strip()
    if refnames.startswith("$Format"):
        return {} # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    for ref in list(refs):
        if not re.search(r'\d', ref):
            refs.discard(ref)
            # Assume all version tags have a digit. git's %d expansion
            # behaves like git log --decorate=short and strips out the
            # refs/heads/ and refs/tags/ prefixes that would let us
            # distinguish between branches and tags. By ignoring refnames
            # without digits, we filter out many common branch names like
            # "release" and "stabilization", as well as "HEAD" and "master".
    for ref in sorted(refs):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            r = ref[len(tag_prefix):]
            return { "version": r,
                     "full": variables["full"].strip() }
    # no suitable tags, so we use the full revision id
    return { "version": variables["full"].strip(),
             "full": variables["full"].strip() }

def versions_from_vcs(tag_prefix, verbose=False):
    # this runs 'git' from the directory that contains this file. That either
    # means someone ran a setup.py command (and this code is in
    # versioneer.py, thus the containing directory is the root of the source
    # tree), or someone ran a project-specific entry point (and this code is
    # in _version.py, thus the containing directory is somewhere deeper in
    # the source tree). This only gets called if the git-archive 'subst'
    # variables were *not* expanded, and _version.py hasn't already been
    # rewritten with a short version string, meaning we're inside a checked
    # out source tree.

    try:
        source_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # some py2exe/bbfreeze/non-CPython implementations don't do __file__
        return {} # not always correct
    GIT = "git"
    if sys.platform == "win32":
        GIT = "git.cmd"
    stdout = run_command([GIT, "describe", "--tags", "--dirty", "--always"],
                         cwd=source_dir)
    if stdout is None:
        return {}
    if not stdout.startswith(tag_prefix):
        if verbose:
            print ("tag '%s' doesn't start with prefix '%s'" % (stdout, tag_prefix))
        return {}
    tag = stdout[len(tag_prefix):]
    stdout = run_command([GIT, "rev-parse", "HEAD"], cwd=source_dir)
    if stdout is None:
        return {}
    full = stdout.strip()
    if tag.endswith("-dirty".encode("utf-8")):
        full += "-dirty".encode("utf-8")
    return {"version": tag, "full": full}

