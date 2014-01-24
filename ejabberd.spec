Summary:	A distributed, fault-tolerant Jabber/XMPP server
Name:		ejabberd
Version:	2.1.13
Release:	1
Group:		System/Servers
License:	GPLv2+
URL:		http://www.ejabberd.im/
Source0:	https://github.com/processone/ejabberd/archive/%{name}-%{version}.tar.gz
Source1:	ejabberd.init
Source3:	inetrc
# http://ejabberd.jabber.ru/ejabberdctl-extra
Source4:	http://ejabberd.jabber.ru/files/efiles/mod_ctlextra.erl
# The following were extracted from a patch found on http://realloc.spb.ru/share/ejabberdad.html
Source5:	ejabberd_auth_ad.erl
Source6:	mod_shared_roster_ad.erl
Source7:	mod_vcard_ad.erl
BuildRequires:	erlang-base
BuildRequires:	erlang-ssl
BuildRequires:	erlang-devel
BuildRequires:	erlang-erl_interface
BuildRequires:	erlang-compiler
BuildRequires:	erlang-asn1
BuildRequires:	libexpat-devel
BuildRequires:	openssl-devel
BuildRequires:	zlib-devel
BuildRequires:	tetex-latex
BuildRequires:	hevea
BuildRequires:	rpm-helper >= 0.21
BuildRequires:	erlang-public_key
BuildRequires:	erlang-parsetools
Requires:	erlang-base
Requires:	erlang-crypto
Requires:	erlang-mnesia
Requires:	erlang-syntax_tools
Requires:	erlang-compiler
Requires:	erlang-asn1
Requires:	erlang-ssl
Requires(pre):         rpm-helper >= 0.21
Requires(post):        rpm-helper >= 0.21
Requires(preun):       rpm-helper >= 0.21
Requires(postun):      rpm-helper >= 0.21

%description
ejabberd is a Free and Open Source distributed fault-tolerant
Jabber/XMPP server. It is mostly written in Erlang, and runs on many
platforms (tested on Linux, FreeBSD, NetBSD, Solaris, Mac OS X and
Windows NT/2000/XP).

%package devel
Summary:	Development files for %{name}
Group:		Development/Other
Requires:	%{name} = %{version}-%{release}
Requires:	erlang-devel

%description devel
Development files for %{name}.

%package doc
Summary:	Documentation for ejabberd
Group:		System/Servers

%description doc
Documentation for ejabberd.

%prep
%setup -q

%{__perl} -pi -e "s!/var/lib/ejabberd!%{_libdir}/ejabberd-%{version}!g" src/Makefile.in
%{__perl} -pi -e "s!/etc!%{_sysconfdir}!g" src/Makefile.in

cp %{SOURCE4} src
cp %{SOURCE5} src
cp %{SOURCE6} src
cp %{SOURCE7} src

%build
%define _disable_ld_no_undefined 1
pushd src
autoreconf -vif
%configure2_5x \
	--enable-odbc \
	--disable-pam \
	--disable-ejabberd_zlib

%make -j1
popd
pushd doc
make html pdf
popd

%install
pushd src
%makeinstall_std
popd

chmod -R a+x %{buildroot}%{_libdir}/ejabberd/priv/lib/

%{__perl} -pi -e 's!./ssl.pem!/etc/pki/tls/private/ejabberd.pem!g' \
    %{buildroot}/etc/ejabberd/ejabberd.cfg

install -d -m 755 %{buildroot}/var/log/ejabberd
install -d -m 755 %{buildroot}%{_var}/lib/ejabberd

install -d -m 755  %{buildroot}%{_initrddir}
install -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/ejabberd

install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} <<'EOF'
/var/log/ejabberd/*.log {
    missingok
    notifempty
    create 0640 ejabberd ejabberd
    sharedscripts
    postrotate
        runuser ejabberd -c "ejabberdctl --node ejabberd@`hostname -s` reopen-log >/dev/null 2>&1" || true
    endscript
}
EOF

cp %{S:3} %{buildroot}%{_sysconfdir}/ejabberd/inetrc

cat > README.urpmi <<EOF
Mandriva RPM specific notes

Post-installation
-----------------
There is no users created with the default configuration.

You have to first create an user, either through a client supporting registration (kopete, psi), or through command line:

$> su ejabberd -c 'ejabberdctl --node ejabberd@host register user domain.tld passwd'

Then you have to grant him admin privilege, by adding such a line in /etc/ejabberd/ejabberd.cfg:

{acl, admin, {user, "user"}}.

More commands are available, through ejabberctl:

$> su ejabberd -c 'ejabberdctl --node ejabberd@host help'

You can also access the web console at http://host:5280/admin
EOF

install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 README %{buildroot}%{_docdir}/%{name}
install -m 644 README.urpmi %{buildroot}%{_docdir}/%{name}
install -m 644 COPYING %{buildroot}%{_docdir}/%{name}
install -m 644 doc/*.pdf doc/*.html doc/*.png doc/release_notes_*  %{buildroot}%{_docdir}/%{name}

install -d -m 755 %{buildroot}%{_sbindir}
# ejabberd wrapper
cat > %{buildroot}%{_sbindir}/ejabberd <<'EOF'
#!/bin/sh

ERLANG_NODE=ejabberd
ERL=/usr/bin/erl
LIB=%{_var}/lib/ejabberd/ebin
CONFIG=/etc/ejabberd/ejabberd.cfg
INETRC=/etc/ejabberd/inetrc
LOG=/var/log/ejabberd/ejabberd.log
SASL_LOG=/var/log/ejabberd/sasl.log
SPOOL=/var/lib/ejabberd

if [ -r /var/lib/ejabberd/.erlang.cookie ] ; then
    export HOME=/var/lib/ejabberd
fi

ARGS=
while [ $# -ne 0 ] ; do
    PARAM=$1
    shift
    case $PARAM in
	--) break ;;
	--node) ERLANG_NODE=$1; shift ;;
	--config) CONFIG=$1 ; shift ;;
	--log) LOG=$1 ; shift ;;
	--sasl-log) SASL_LOG=$1 ; shift ;;
	--spool) SPOOL=$1 ; shift ;;
	*) ARGS="$ARGS $PARAM" ;;
    esac
done

if [ "$ERLANG_NODE" = "${ERLANG_NODE%.*}" ] ; then
    SNAME=-sname
else
    SNAME=-name
fi

exec $ERL -pa $LIB \
    $SNAME $ERLANG_NODE \
    -s ejabberd \
    -kernel inetrc \"$INETRC\" \
    -ejabberd config \"$CONFIG\" log_path \"$LOG\" \
    -sasl sasl_error_logger \{file,\"$SASL_LOG\"\} \
    -mnesia dir \"$SPOOL\" \
    $ERL_OPTIONS $ARGS "$@"
EOF
chmod 755 %{buildroot}%{_sbindir}/ejabberd

%pre
if [ -d %{_var}/lib/%{name}/spool ]; then
    mv -f %{_var}/lib/%{name}/spool/* %{_var}/lib/%{name}
    rmdir %{_var}/lib/%{name}/spool
fi
%_pre_useradd ejabberd /var/lib/ejabberd /bin/sh
%_pre_groupadd ejabberd ejabberd

%preun
%_preun_service ejabberd

%post
%_create_ssl_certificate ejabberd -b -g ejabberd
%_post_service ejabberd

%postun
%_postun_userdel ejabberd
%_postun_groupdel ejabberd

%files
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/README
%{_docdir}/%{name}/README.urpmi
%dir %attr(750,root,ejabberd) %{_sysconfdir}/ejabberd
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberd.cfg
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/inetrc
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberdctl.cfg
%{_initrddir}/ejabberd
%{_sbindir}/ejabberd
%attr(550,root,ejabberd) %{_sbindir}/ejabberdctl
%dir %{_libdir}/ejabberd
%dir %{_libdir}/ejabberd/ebin
%dir %{_libdir}/ejabberd/priv
%{_libdir}/ejabberd/ebin/*
%{_libdir}/ejabberd/priv/*
%config(noreplace) %{_sysconfdir}/logrotate.d/ejabberd
%attr(-,ejabberd,ejabberd) /var/lib/ejabberd
%attr(-,ejabberd,ejabberd) /var/log/ejabberd

%files devel
%defattr(-,root,root)
%{_libdir}/ejabberd/include

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}
%exclude %{_docdir}/%{name}/COPYING
%exclude %{_docdir}/%{name}/README
%exclude %{_docdir}/%{name}/README.urpmi


%changelog
* Wed Apr 21 2010 Funda Wang <fwang@mandriva.org> 2.1.3-2mdv2010.1
+ Revision: 537457
- rebuild

* Mon Mar 29 2010 Tomasz Pawel Gajc <tpg@mandriva.org> 2.1.3-1mdv2010.1
+ Revision: 528656
- update to new version 2.1.3

* Thu Mar 04 2010 Tiago Salem <salem@mandriva.com.br> 2.1.2-3mdv2010.1
+ Revision: 514148
- fix wrong permissions. Add/remove ejabberd group.

* Wed Feb 24 2010 Tomasz Pawel Gajc <tpg@mandriva.org> 2.1.2-2mdv2010.1
+ Revision: 510688
- fix chown/chmod on ejabber config files
- tune up init file

* Mon Jan 18 2010 Frederik Himpe <fhimpe@mandriva.org> 2.1.2-1mdv2010.1
+ Revision: 493241
- update to new version 2.1.2

* Wed Dec 30 2009 Frederik Himpe <fhimpe@mandriva.org> 2.1.1-1mdv2010.1
+ Revision: 483988
- update to new version 2.1.1

* Thu Nov 19 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.1.0-1mdv2010.1
+ Revision: 467486
- update to new version 2.1.0
- move headers to devel subpackage
- shared objects are now in %%{_libdir}

* Wed Jun 17 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.5-2mdv2010.0
+ Revision: 386832
- rebuild for new erlang

* Fri May 01 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.5-1mdv2010.0
+ Revision: 369966
- update to new version 2.0.5

* Fri Apr 24 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.4-2mdv2010.0
+ Revision: 369027
- add missing requires on erlang-ssl and erlang-asn1 (mdvbz #50254)

* Wed Mar 18 2009 Frederik Himpe <fhimpe@mandriva.org> 2.0.4-1mdv2009.1
+ Revision: 357204
- update to new version 2.0.4

* Tue Jan 27 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.3-1mdv2009.1
+ Revision: 334681
- update to new version 2.0.3

* Thu Nov 06 2008 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.2-2mdv2009.1
+ Revision: 300330
- add requires on erlang-syntax_tools and erlang-compiler (#45249)

* Wed Sep 03 2008 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.2-1mdv2009.0
+ Revision: 279387
- update to new version 2.0.2

* Thu Jul 24 2008 Thierry Vignaud <tv@mandriva.org> 2.0.1-2mdv2009.0
+ Revision: 244654
- rebuild

* Tue Jul 22 2008 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.1-1mdv2009.0
+ Revision: 240217
- use %%define _disable_ld_no_undefined 1
- don't use parallel make as it crashes
- use %%_var instead of %%_localstatedir
- fix file list
- update to new version 2.0.1

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Wed Feb 27 2008 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.0-1mdv2008.1
+ Revision: 175952
- update:
  o mod_vcard_ad.erl
  o ejabberd_auth_ad.er
  o mod_ctlextra.erl
  o mod_shared_roster_ad.erl
- correct urls
- new version

* Fri Feb 15 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.0.0-0.rc1.2mdv2008.1
+ Revision: 168825
- bump rpm-helper versionned build dependency

* Tue Feb 05 2008 Tomasz Pawel Gajc <tpg@mandriva.org> 2.0.0-0.rc1.1mdv2008.1
+ Revision: 162903
- add missing build requires on erlang-compiler, erlang-erl_interface and erlang-asn1
- enable parallel build

  + Guillaume Rousse <guillomovitch@mandriva.org>
    - use new create ssl certificate helper macro interface
    - new version

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Tue Oct 09 2007 Jérôme Soyer <saispo@mandriva.org> 1.1.4-1mdv2008.1
+ Revision: 96042
- New release 1.1.4

  + Guillaume Rousse <guillomovitch@mandriva.org>
    - fix logrotate configuration

* Sat Jun 30 2007 Guillaume Rousse <guillomovitch@mandriva.org> 1.1.3-6mdv2008.0
+ Revision: 45946
- disable parallel build
- use new ssl certificate creation helper
- ldaps support

* Wed Jun 27 2007 Guillaume Rousse <guillomovitch@mandriva.org> 1.1.3-5mdv2008.0
+ Revision: 45216
- handle migration of database from %%{_localstatedir}/%%{name}/spool to %%{_localstatedir}/%%{name}
- add erlang-crypto and erlang-mnesia as minimal dependencies
- set HOSTNAME env var before creating ssl certs, as  it may not be defined
- set HOME in wrappers too
- use wrappers in init script and in logrotate configuration
- additional wrapper for ejabberd
- add an ejabberdctl wrapper, based on debian one
- handle ssl certs in standard way
- give a real shell for ejabberd user, as most operations requires it
- handle doc manually, as %%doc macro sux, and use a herein document for README.urpmi
- clean up file list, and sanitize perms to standard default values

* Sun Jun 17 2007 Tomasz Pawel Gajc <tpg@mandriva.org> 1.1.3-4mdv2008.0
+ Revision: 40522
- rebuild for erlang
- spec file clean

* Sun Jun 03 2007 Gustavo De Nardin <gustavodn@mandriva.com> 1.1.3-2mdv2008.0
+ Revision: 34803
- fixed init script LSB headers
- requires erlang-base
- -doc package does not requires hevea


* Sat Mar 10 2007 Oden Eriksson <oeriksson@mandriva.com> 1.1.3-1mdv2007.1
+ Revision: 140380
- fix deps

  + Jérôme Soyer <saispo@mandriva.org>
    - Release 1.1.3

  + Michael Scherer <misc@mandriva.org>
    - fix description
    - version 1.1.2, and use a .tar.bz2
    - correct status action of the initscript
    - Import ejabberd

* Wed Aug 16 2006 Jerome Soyer <saispo@mandriva.org> 1.1.1-3mdv2007.0
- Fix initscript
- Fix ejabberd.cfg

* Mon Aug 14 2006 Jerome Soyer <saispo@mandriva.org> 1.1.1-2mdv2007.0
- Fix #23697, #23698
- Update Requires
- Add cert file

* Wed Jul 05 2006 Jerome Soyer <saispo@mandriva.org> 1.1.1-1mdv2007.0
- Rediff all the spec from FC spec

* Fri Jun 09 2006 Jerome Soyer <saispo@mandriva.org> 1.0.0-1mdv2007.0
- Initial Mandriva Package

