Summary:	A distributed, fault-tolerant Jabber/XMPP server

Name:		ejabberd
Version:	2.1.13
Release:	4
Group:		System/Servers
License:	GPLv2+
URL:		http://www.ejabberd.im/
Source0:	http://www.process-one.net/downloads/ejabberd/%{version}/%{name}-%{version}.tgz
Source3:        inetrc
# http://ejabberd.jabber.ru/ejabberdctl-extra
Source4:	http://ejabberd.jabber.ru/files/efiles/mod_ctlextra.erl
# The following were extracted from a patch found on http://realloc.spb.ru/share/ejabberdad.html
Source5:	ejabberd_auth_ad.erl
Source6:	mod_shared_roster_ad.erl
Source7:	mod_vcard_ad.erl

Source9:        ejabberd.logrotate
Source10:       ejabberd.sysconfig
Source11:       ejabberd.service
Source12:       ejabberd.tmpfiles.conf

# PAM support
Source13:       ejabberdctl.pam
Source14:       ejabberdctl.apps
Source15:       ejabberd.pam

# Patches from Fedora
# Use ejabberd as an example for PAM service name (fedora/epel-specific)
Patch1: ejabberd-0001-Fix-PAM-service-example-name-to-match-actual-one.patch
# fixed delays in s2s connections
Patch2: ejabberd-0002-Fixed-delays-in-s2s-connections.patch
# Introducing mod_admin_extra
Patch3: ejabberd-0003-Introducing-mod_admin_extra.patch
# BZ# 439583, 452326, 451554, 465196, 502361 (fedora/epel-specific)
Patch4: ejabberd-0004-Fedora-specific-changes-to-ejabberdctl.patch
# Fix so-lib permissions while installing (fedora/epel-specific)
Patch5: ejabberd-0005-Install-.so-objects-with-0755-permissions.patch
# Will be proposed for inclusion into upstream
Patch6: ejabberd-0006-Use-versioned-directory-for-storing-docs.patch
# Backported from upstream
Patch7: ejabberd-0007-Support-SASL-GSSAPI-authentication-thanks-to-Mikael-.patch
# Disable IP restriction for ejabberdctl (seems that it doesn't work well)
Patch8: ejabberd-0008-Disable-INET_DIST_INTERFACE-by-default.patch

BuildRequires:	erlang-base
BuildRequires:	erlang-ssl
BuildRequires:	erlang-devel
BuildRequires:	erlang-erl_interface
BuildRequires:	erlang-compiler
BuildRequires:	erlang-asn1
BuildRequires:	erlang-public_key
BuildRequires:	erlang-parsetools
BuildRequires:	libexpat-devel
BuildRequires:	openssl-devel
BuildRequires:	zlib-devel
BuildRequires:	tetex-latex
BuildRequires:	hevea
BuildRequires:	rpm-helper >= 0.21
BuildRequires:  texlive-collection-basic
Requires:	erlang-base
Requires:	erlang-crypto
Requires:	erlang-mnesia
Requires:	erlang-syntax_tools
Requires:	erlang-compiler
Requires:	erlang-asn1
Requires:	erlang-ssl
Requires(post):	systemd
Requires(pre):	rpm-helper >= 0.19
Requires(post):	rpm-helper >= 0.21
Requires(preun):	rpm-helper >= 0.19
Requires(postun):	rpm-helper >= 0.19


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


%patch1 -p1 -b .pam_name
%patch2 -p1 -b .s2s_delays
%patch3 -p1 -b .mod_admin_extra
#%patch4 -p1 -b .fedora_specific
%patch5 -p1 -b .fix_perms
%patch6 -p1 -b .versioned_docdir
%patch7 -p1 -b .gssapi
%patch8 -p1 -b .disable_ip_restriction_for_ejabberdctl

# FIXME one more last-minute fix, now for 2.1.13
sed -i -e "s,2.1.12,2.1.13,g" src/configure
touch -r src/configure.ac src/configure

%{__perl} -pi -e "s!/var/lib/ejabberd!%{_libdir}/ejabberd-%{version}!g" src/Makefile.in
%{__perl} -pi -e "s!/etc!%{_sysconfdir}!g" src/Makefile.in

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
pushd src
%makeinstall_std
popd

# fix example SSL certificate path to real one, which we created recently (see above)
%{__perl} -pi -e 's!/path/to/ssl.pem!/etc/ejabberd/ejabberd.pem!g' %{buildroot}/etc/ejabberd/ejabberd.cfg

# fix captcha path
%{__perl} -pi -e 's!/lib/ejabberd/priv/bin/captcha.sh!%{_libdir}/%{name}/priv/bin/captcha.sh!g' %{buildroot}/etc/ejabberd/ejabberd.cfg

mkdir -p %{buildroot}/var/log/ejabberd
mkdir -p %{buildroot}/var/lib/ejabberd/spool

chmod a+x %{buildroot}%{_libdir}/ejabberd/priv/lib/

%{__perl} -pi -e 's!./ssl.pem!/etc/pki/tls/private/ejabberd.pem!g' \
    %{buildroot}/etc/ejabberd/ejabberd.cfg

install -d -m 755 %{buildroot}/var/log/ejabberd
install -d -m 755 %{buildroot}%{_var}/lib/ejabberd

# install systemd entry
install -D -m 0644 -p %{S:11} %{buildroot}%{_unitdir}/%{name}.service
install -D -m 0644 -p %{S:12} %{buildroot}%{_tmpfilesdir}/%{name}.conf

# install sysconfig file
install -D -p -m 0644  %{S:10} %{buildroot}%{_sysconfdir}/sysconfig/ejabberd

mkdir -p %{buildroot}%{_bindir}
ln -s consolehelper %{buildroot}%{_bindir}/ejabberdctl
install -D -p -m 0644 %{S:13} %{buildroot}%{_sysconfdir}/pam.d/ejabberdctl
install -D -p -m 0644 %{S:14} %{buildroot}%{_sysconfdir}/security/console.apps/ejabberdctl
install -D -p -m 0644 %{S:15} %{buildroot}%{_sysconfdir}/pam.d/ejabberd


# install config for logrotate
install -D -p -m 0644  %{S:9} %{buildroot}%{_sysconfdir}/logrotate.d/ejabberd

cp %{S:3} %{buildroot}%{_sysconfdir}/ejabberd/inetrc

cat > README.urpmi <<EOF
Mageia RPM specific notes

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
%_pre_useradd %{name} /var/lib/%{name} /bin/sh
%_pre_groupadd %{name} %{name}

%preun
%_preun_service %{name}

%post
%_create_ssl_certificate %{name} -b -g %{name}
%_tmpfilescreate %{name}
%_post_service %{name}

%postun
%_postun_userdel %{name}
%_postun_groupdel %{name}

%clean

%files
%doc %{_docdir}/%{name}-%{version}
%{_docdir}/%{name}/COPYING
%{_docdir}/%{name}/README
%{_docdir}/%{name}/README.urpmi
%dir %attr(750,root,ejabberd) %{_sysconfdir}/ejabberd
%attr(750,root,ejabberd) %{_sysconfdir}/sysconfig/ejabberd
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberd.cfg
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/inetrc
%attr(640,root,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberdctl.cfg
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%{_sbindir}/ejabberd
%config(noreplace) %{_sysconfdir}/pam.d/%{name}
%config(noreplace) %{_sysconfdir}/pam.d/ejabberdctl
%config(noreplace) %{_sysconfdir}/security/console.apps/ejabberdctl
%{_bindir}/ejabberdctl
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
%{_libdir}/ejabberd/include

%files doc
%{_docdir}/%{name}/*
%exclude %{_docdir}/%{name}/COPYING
%exclude %{_docdir}/%{name}/README
%exclude %{_docdir}/%{name}/README.urpmi
