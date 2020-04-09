# specfile to build a memcached package for use with EasyApache

%global username   memcached
%global groupname  memcached
%global binname memcached

%if 0%{?centos} >= 7 || 0%{?fedora} >= 17 || 0%{?rhel} >= 7
%global with_systemd 1
%else
%global with_systemd 0
%endif

Name: ea-memcached
Version: 1.5.16

Summary: memcached daemon
%define release_prefix 2
Release: %{release_prefix}%{?dist}.cpanel
License: MIT
Group: Programming/Languages
URL: https://www.memcached.org/
Source: http://www.memcached.org/files/memcached-%{version}.tar.gz
Source1: memcached.env
# init script for sysv systems
Source2: memcached.sysv
# unit file for systemd systems
Source3: memcached.service

Patch1: memcached-unit.patch

BuildRequires: libevent-devel cyrus-sasl-devel

%if %{with_systemd}
BuildRequires: systemd-units
BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
# For triggerun
Requires(post): systemd-sysv
%else
BuildRequires: chkconfig
Requires: initscripts
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig, /sbin/service
Requires(postun): /sbin/service
%endif
Requires(pre):  shadow-utils

# as of 3.5.5-4 selinux has memcache included
Obsoletes: memcached-selinux

# Don't conflict with other memcached packages since we install to the same
# place. Allow other packages dependent on memcached to install.
Provides: memcached

%description
memcached is a high-performance, distributed memory object caching
system, generic in nature, but intended for use in speeding up dynamic
web applications by alleviating database load.


%package devel
Summary:	Files needed for development using memcached protocol
Group:		Development/Libraries
Requires:	%{name} = %{version}-%{release}

%description devel
Install memcached-devel if you are developing C/C++ applications that require
access to the memcached binary include files.

%prep
%setup -n memcached-%{version}
%patch1 -p1 -b .unit

%build
./configure --prefix=%{buildroot}/%{_usr} --enable-sasl
make

#%check
#make test

%install
# install binaries
make install INSTALL_ROOT=%{buildroot}

# install config
install -m 755 -d %{buildroot}/%{_sysconfdir}
mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig
install -pm 644 %{SOURCE1} %{buildroot}/%{_sysconfdir}/sysconfig/memcached

%if %{with_systemd}
  mkdir -p %{buildroot}%{_unitdir}
  install -pm 644 %{SOURCE3} %{buildroot}%{_unitdir}/%{binname}.service
%else
  mkdir -p %{buildroot}%{_initddir}
  install -pm 755 %{SOURCE2} %{buildroot}%{_initddir}/%{binname}
  # pid directory
  install -m 755 -d %{buildroot}/%{_localstatedir}/run/%{binname}
%endif

%pre
getent group %{groupname} >/dev/null || groupadd -r %{groupname}

%if %{with_systemd}
  getent passwd %{username} >/dev/null || useradd \
    -r -g %{groupname} -d /run/%{binname} \
    -s /sbin/nologin -c "Memcached daemon" %{username}
%else
  getent passwd %{username} >/dev/null || useradd \
    -r -g %{groupname} -d %{_localstatedir}/run/%{binname} \
    -s /sbin/nologin -c "Memcached daemon" %{username}
%endif


%post
%if %{with_systemd}
  %systemd_post %{binname}.service
  if [ $1 -eq 1 ] ; then
    systemctl start %{binname}
  fi
%else
  /sbin/chkconfig --add %{binname}
  if [ $1 -eq 1 ] ; then
    service %{binname} restart
  fi
%endif


%preun
%if %{with_systemd}
  %systemd_preun %{binname}.service
%else
    /sbin/service %{binname} stop > /dev/null 2>&1
    /sbin/chkconfig --del %{binname}
%endif


%postun
%if %{with_systemd}
  %systemd_postun_with_restart %{binname}.service
%else
    /sbin/service %{binname} restart &> /dev/null
%endif

%triggerun -- memcached
%if %{with_systemd}
  if [[ -f /etc/rc.d/init.d/memcached ]]; then
    # Run these because the SysV package being removed won't do them
    /sbin/chkconfig --del memcached >/dev/null 2>&1 || :
    /bin/systemctl stop memcached.service >/dev/null 2>&1 || :
  fi
%endif

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/sysconfig/memcached
%{_bindir}/memcached
%{_mandir}/man1/memcached.1*
%if %{with_systemd}
  %{_unitdir}/memcached.service
%else
  %{_initddir}/memcached
  %dir %attr(755,%{username},%{groupname}) %{_localstatedir}/run/memcached
%endif

%files devel
%defattr(-,root,root,-)
%{_includedir}/memcached/*

%changelog
* Wed Apr 08 2020 Daniel Muey <dan@cpanel.net> - 1.5.16-2
- ZC-6515: Promote from experimental
- ZC-6537: start daemon after install

* Fri Jun 14 2019 Tim Mullin <tim@cpanel.net> - 1.5.16-1
- EA-8224: Updated to 1.5.16 from upstream

* Tue Apr 16 2019 Andy Baugh <thomas.baugh@cpanel.net> - 1.5.12-2
- CPANEL-26786: Add "provides" entry for memcached, as we actually conflict
  with the base package due to installing to the same place (but it is the
  same software package ultimately, so may as well have it act as an
  alternative instead of conflicting).

* Thu Nov 08 2018 Cory McIntire <cory@cpanel.net> - 1.5.12-1
- EA-7981: update to version 1.5.12

* Fri Jan 12 2018 Cory McIntire <cory@cpanel.net> - 1.5.3-2
- EA-7058: Fix devel Require to match package name

* Wed Dec 06 2017 Cory McIntire <cory@cpanel.net> - 1.5.3-1
- EA-6996: Update version and enable systemd calls on CentOS 7

* Wed Jul 24 2017 Jack Hayhurst <jakdept@gmail.com> - 1.4.35-4
- Change config install location in spec file to match init files
- modified from github PR #1, also fixed changelog versions

* Wed Mar 8 2017 Jacob Perkins <jacob.perkins@cpanel.net> - 1.4.35-3
- Enabled SASL support

* Fri Mar  3 2017 Jack Hayhurst <jakdept@gmail.com> - 1.4.35-2
- reworked a lot of paths in the specfile - it should now be working

* Fri Mar  3 2017 Jack Hayhurst <jakdept@gmail.com> - 1.4.35-1
- initial spec file creation
