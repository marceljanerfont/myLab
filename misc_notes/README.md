# misc_notes
miscellaneous notes

## Set up Dev env C++ in OS X El capitan
* open terminal and type 'gcc', then it will ask to install command-line developer tools
* install MacPorts: https://www.macports.org/install.php (should be located at /opt/local/bin
* install CGAL libraries:

          sudo port install cgal
          sudo port install cgal +qt5 +universal +demos # with the demos

* download CGAL source from https://github.com/CGAL/cgal/releases, and uncompress it to: /opt/local/CGAL-4.7
* open cmake-gui 3.5 (http://www.cmake.org/) use Unix Makefiles
    * Where is the source code: /opt/local/CGAL-4.7
    * Where to build the binaries: /Users/xxx/CGAL-4.7
    * Configure and Generate
* open terminal in /Users/xxx/CGAL-4.7
* make examples
* make demos (Qt5 need it)
