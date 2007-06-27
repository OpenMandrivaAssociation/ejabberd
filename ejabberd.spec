Name:		ejabberd
Version:	1.1.3
Release:    %mkrel 4
Summary:	A distributed, fault-tolerant Jabber/XMPP server
Group:		System/Servers
License:	GPL
URL:		http://ejabberd.jabber.ru/
Source0:	http://www.process-one.net/en/projects/ejabberd/download/%{version}/ejabberd-%{version}.tar.bz2
Source1:	ejabberd.init
Source2:	ejabberd.logrotate
Source3:	inetrc

# http://ejabberd.jabber.ru/ejabberdctl-extra
Source4:	http://ejabberd.jabber.ru/files/efiles/mod_ctlextra.erl

# The following were extracted from a patch found on http://realloc.spb.ru/share/ejabberdad.html
Source5:	ejabberd_auth_ad.erl
Source6:	mod_shared_roster_ad.erl
Source7:	mod_vcard_ad.erl
Source8:	gencert.sh
BuildRequires:	erlang-stack
BuildRequires:	erlang-devel
BuildRequires:	libexpat-devel
BuildRequires:	openssl-devel
BuildRequires:	zlib-devel
BuildRequires:	tetex-latex
BuildRequires:	hevea
Requires:	    erlang-base
Requires(pre):	rpm-helper
BuildRoot:	    %{_tmppath}/%{name}-%{version}

%description
ejabberd is a Free and Open Source distributed fault-tolerant
Jabber/XMPP server. It is mostly written in Erlang, and runs on many
platforms (tested on Linux, FreeBSD, NetBSD, Solaris, Mac OS X and
Windows NT/2000/XP).

%package doc
Summary:	Documentation for ejabberd
Group:		System/Servers

%description doc
Documentation for ejabberd.

%pre
%_pre_useradd ejabberd /var/lib/ejabberd /sbin/nologin

%preun
%_preun_service ejabberd

%postun
%_postun_userdel ejabberd

%prep
%setup -q

%{__perl} -pi -e "s!/var/lib/ejabberd!%{_libdir}/ejabberd-%{version}!g" src/Makefile.in
%{__perl} -pi -e "s!/etc!%{_sysconfdir}!g" src/Makefile.in
%{__perl} -pi -e "s!\@prefix\@!!g" src/Makefile.in

cp %{SOURCE4} src
cp %{SOURCE5} src
cp %{SOURCE6} src
cp %{SOURCE7} src

%build
pushd src
%configure2_5x \
	--enable-odbc
%make
popd
pushd doc
make html pdf
popd

%install
rm -rf %{buildroot}
pushd src
%makeinstall_std
popd

chmod a+x %{buildroot}%{_libdir}/ejabberd-%{version}/priv/lib/*.so

%{__perl} -pi -e 's!./ssl.pem!/etc/ssl/ejabberd/ejabberd.pem!g' %{buildroot}/etc/ejabberd/ejabberd.cfg

mkdir -p %{buildroot}/var/log/ejabberd
mkdir -p %{buildroot}/var/lib/ejabberd/spool

mkdir -p %{buildroot}%{_initrddir}
cp %{S:1} %{buildroot}%{_initrddir}/ejabberd
chmod a+x %{buildroot}%{_initrddir}/ejabberd

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
cp %{S:2} %{buildroot}%{_sysconfdir}/logrotate.d/ejabberd

%{__perl} -pi -e 's!\@libdir\@!%{_libdir}!g' %{buildroot}%{_initrddir}/ejabberd %{buildroot}%{_sysconfdir}/logrotate.d/ejabberd
%{__perl} -pi -e 's!\@version\@!%{version}!g' %{buildroot}%{_initrddir}/ejabberd %{buildroot}%{_sysconfdir}/logrotate.d/ejabberd

cp %{S:3} %{buildroot}%{_sysconfdir}/ejabberd/inetrc

mkdir -p %{buildroot}/%{_datadir}/%{name}
install -m 755 %{SOURCE8} %{buildroot}/%{_datadir}/%{name}

mkdir -p %{buildroot}/%{_sysconfdir}/ssl/%{name}

cat > README.urpmi <<EOF
Mandriva RPM specific notes

Post-installation
-----------------
There is no users created with the default configuration.

You have to first create an user, either through a client supporting registration (kopete, psi), or through command line:

$> su ejabberd -c 'erl -pa /usr/lib/ejabberd-%{version}/ebin -noinput -sname \
$> ejabberdctl -s ejabberd_ctl -extra ejabberd@host register foo domain.com \
$> myadminpass'

Then you have to grant him admin privilege, by adding such a line in /etc/ejabberd/ejabberd.cfg:

{acl, admin, {user, "foo"}}.

More commands are available, through ejabberctl:

$> su ejabberd -c 'erl -pa /usr/lib/ejabberd-%{version}/ebin -noinput -sname \
$> ejabberdctl -s ejabberd_ctl -extra ejabberd@host help'

You can also access the web console at http://host:5280/admin
EOF

install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 README.urpmi %{buildroot}%{_docdir}/%{name}
install -m 644 TODO %{buildroot}%{_docdir}/%{name}
install -m 644 ChangeLog %{buildroot}%{_docdir}/%{name}
install -m 644 COPYING %{buildroot}%{_docdir}/%{name}
install -m 644 doc/*.pdf doc/*.html doc/*.png doc/release_notes_*  %{buildroot}%{_docdir}/%{name}

%post

mkdir -p %{_sysconfdir}/ssl/%{name}
# generate the ejabberd.pem cert here instead of the initscript                                                                                                                                                                                  
if [ ! -e %{_sysconfdir}/ssl/%{name}/ejabberd.pem ] ; then
  if [ -x %{_datadir}/%{name}/gencert.sh ] ; then
    echo "Generating self-signed certificate..."
    pushd %{_sysconfdir}/ssl/%{name}/ > /dev/null
    yes ""|%{_datadir}/%{name}/gencert.sh >/dev/null 2>&1
    chmod 640 ejabberd.pem
    chown root:ejabberd ejabberd.pem
    popd > /dev/null
  fi
  echo "To re-generate a self-signed certificate, you can use the utility"
  echo "%{_datadir}/%{name}/gencert.sh..."
  echo "(Do it at least once for having the right information in  %{_sysconfdir}/ssl/%{name}/"
fi

%_post_service ejabberd

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/ChangeLog
%{_docdir}/%{name}/TODO
%{_docdir}/%{name}/README.urpmi
%dir %{_sysconfdir}/ejabberd
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberd.cfg
%config(noreplace) %{_sysconfdir}/ejabberd/inetrc
%{_initrddir}/ejabberd
%config(noreplace) %{_sysconfdir}/logrotate.d/ejabberd
%{_libdir}/ejabberd-%{version}
%attr(-,ejabberd,ejabberd) /var/lib/ejabberd
%attr(-,ejabberd,ejabberd) /var/log/ejabberd
%{_datadir}/%{name}/gencert.sh

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}
%exclude %{_docdir}/%{name}/COPYING
%exclude %{_docdir}/%{name}/ChangeLog
%exclude %{_docdir}/%{name}/TODO
%exclude %{_docdir}/%{name}/README.urpmi
