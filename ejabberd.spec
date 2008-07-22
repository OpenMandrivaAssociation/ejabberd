Name:		ejabberd
Version:	2.0.1
Release:	%mkrel 1
Summary:	A distributed, fault-tolerant Jabber/XMPP server
Group:		System/Servers
License:	GPLv2+
URL:		http://www.ejabberd.im/
Source0:	http://www.process-one.net/downloads/ejabberd/%{version}/%{name}-%{version}_2.tar.gz
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
Requires:	erlang-base
Requires:	erlang-crypto
Requires:	erlang-mnesia
Requires(pre):	rpm-helper >= 0.19
Requires(post):	rpm-helper >= 0.21
Requires(preun):	rpm-helper >= 0.19
Requires(postun):	rpm-helper >= 0.19
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

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
%define _disable_ld_no_undefined 1
pushd src
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
rm -rf %{buildroot}
pushd src
%makeinstall_std
popd

chmod a+x %{buildroot}%{_var}/lib/ejabberd/priv/lib/*.so

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
install -m 644 ChangeLog %{buildroot}%{_docdir}/%{name}
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

%preun
%_preun_service ejabberd

%post
%_create_ssl_certificate ejabberd -b -g ejabberd
%_post_service ejabberd

%postun
%_postun_userdel ejabberd

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/ChangeLog
%{_docdir}/%{name}/README
%{_docdir}/%{name}/README.urpmi
%dir %{_sysconfdir}/ejabberd
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberd.cfg
%config(noreplace) %{_sysconfdir}/ejabberd/inetrc
%config(noreplace) %{_sysconfdir}/ejabberd/ejabberdctl.cfg
%{_initrddir}/ejabberd
%{_sbindir}/ejabberd
%{_sbindir}/ejabberdctl
%config(noreplace) %{_sysconfdir}/logrotate.d/ejabberd
%attr(-,ejabberd,ejabberd) /var/lib/ejabberd
%attr(-,ejabberd,ejabberd) /var/log/ejabberd

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}
%exclude %{_docdir}/%{name}/COPYING
%exclude %{_docdir}/%{name}/ChangeLog
%exclude %{_docdir}/%{name}/README
%exclude %{_docdir}/%{name}/README.urpmi
