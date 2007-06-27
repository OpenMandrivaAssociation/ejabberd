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
Source9:	ejabberd.README.urpmi
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
install -m 644 %{SOURCE9} %{buildroot}/%{_datadir}/%{name}/

mkdir -p %{buildroot}/%{_sysconfdir}/ssl/%{name}


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
%doc COPYING
%doc %{_datadir}/%{name}/ejabberd.README.urpmi
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
%doc ChangeLog COPYING TODO doc/*.pdf doc/*.html doc/*.png doc/release_notes_*
