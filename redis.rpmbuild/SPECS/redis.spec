Name:           redis
Version:        2.8.13
Release:        3%{?dist}
Summary:        Redis Database

Group:          Redis Database
License:        BSD
URL:            http://redis.io
Source0:        http://download.redis.io/releases/%{name}-%{version}.tar.gz

BuildRequires:  gcc, tcl

%define         _topdir   %{getenv:HOME}/work/packages/%{name}.rpmbuild
%define         pid_dir   %{_localstatedir}/run/%{name}
%define         pid_file  %{pid_dir}/%{name}.pid
%define         redis_dir /usr/local/%{name}

%description


%prep
%setup -q

%{__cat} <<EOF >%{name}.logrotate
%{redis_dir}/log/*log {
    missingok
}
EOF

%{__cat} <<'EOF' >%{name}.sysv
#!/bin/sh
#
# Simple Redis init.d script conceived to work on Linux systems
# as it does use of the /proc filesystem.
#
# chkconfig:   - 99 01 
# description: Redis Database Server
# processname: %{name}
# config:      %{_sysconfdir}/redis.conf
# pidfile:     %{pid_file}


# -- source function library
. /etc/rc.d/init.d/functions

# -- bootstrap directory for redis.
REDIS_BASE_DIR=%{redis_dir}

REDISPORT=6379
EXEC=%{redis_dir}/sbin/redis-server
CLIEXEC=redis-cli
CONF="%{_sysconfdir}/redis.conf"

PIDFILE=%{pid_file}
RUNUSER=%{name}

cd $REDIS_BASE_DIR

case "$1" in
  start)
    if [ -f $PIDFILE ]
    then
      echo "$PIDFILE exists, process is already running or crashed"
    else
      ulimit -n 10032
      echo -n "Starting Redis server..."
      daemon --user $RUNUSER --pidfile $PIDFILE $EXEC $CONF
      echo
    fi
    ;;
  stop)
    if [ ! -f $PIDFILE ]
    then
      echo "$PIDFILE does not exist, process is not running"
    else
      PID=$(cat $PIDFILE)
      echo -n "Stopping ... "
      $CLIEXEC -p $REDISPORT shutdown

      while { ps -p $PID > /dev/null 2>&1; }
      do
        echo "Waiting for Redis to shutdown ..."
        sleep 1
      done
      echo "Redis stopped"
    fi
    ;;
  *)
    echo "Please use start or stop as first argument"
    ;;
esac
EOF


%build
make %{?_smp_mflags}
cp redis.conf redis.conf.ori
sed -e "s/^daemonize no$/daemonize yes/" -e "s:^logfile .*:logfile %{redis_dir}/log/%{name}.log:" -e "s:^pidfile .*:pidfile %{pid_file}:" redis.conf.ori > %{name}.conf

%check
#make test

%install
%{__rm} -rf %{buildroot}
make PREFIX=%{buildroot}%{redis_dir} install

%{__install} -Dp -m 0755 %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -Dp -m 0755 %{name}.sysv %{buildroot}%{_sysconfdir}/init.d/%{name}
%{__install} -Dp -m 0755 %{name}.conf %{buildroot}%{_sysconfdir}/%{name}.conf

%{__install} -p -d -m 0755 %{buildroot}%{redis_dir}/sbin
%{__install} -p -d -m 0755 %{buildroot}%{redis_dir}/log
%{__install} -p -d -m 0755 %{buildroot}%{pid_dir}

%{__mv} %{buildroot}%{redis_dir}/bin/redis-server %{buildroot}%{redis_dir}/sbin

%pre
getent group  %{name} &> /dev/null || groupadd -r %{name} &> /dev/null
getent passwd %{name} &> /dev/null || \
  useradd -r -s /sbin/nologin -d %{redis_dir} -c '%{name} server' -g %{name} %{name} &> /dev/null

SYSCTL=%{_sysconfdir}/sysctl.conf
cp $SYSCTL $SYSCTL.ori
if [ 1 -le `cat %{_sysconfdir}/sysctl.conf | grep 'vm.overcommit_memory' | wc -l ` ]; then
  sed -e "s/^vm.overcommit_memory .*/vm.overcommit_memory = 1/" $SYSCTL.ori > $SYSCTL
else
  echo ""                                          >> $SYSCTL
  echo "# -- redis memory overcommit requirement." >> $SYSCTL
  echo "vm.overcommit_memory = 1"                  >> $SYSCTL
fi

exit 0

%post
/sbin/chkconfig --add %{name}
cd %{redis_dir}; ln -s %{_sysconfdir}/%{name}.conf; chown -R root:root sbin
cd %{_bindir}; ln -s %{redis_dir}/bin/redis-cli

%preun
if [ $1 = 0 ]; then
  /sbin/service %{name} stop > /dev/null 2>&1
  /sbin/chkconfig --del %{name}

  chown -R redis:redis %{redis_dir}/sbin
  rm -f %{_bindir}/redis-cli

  if [ -h "%{redis_dir}/%{name}.conf" ]; then
    rm -f %{redis_dir}/%{name}.conf
  fi
fi


%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-,%{name},%{name},-)
%doc
%dir %attr(0755,%{name},%{name}) %{redis_dir}
%{redis_dir}/*
%{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %attr(0644,root,root) %{_sysconfdir}/%{name}.conf
%attr(0755,root,root) %{_sysconfdir}/init.d/%{name}

%dir %attr(0755,%{name},%{name}) %{_localstatedir}/run/%{name}


%changelog
* Mon Jul 21 2014 Stephane Peiry <stephane@pittypanda.com> 2.8.13-1.0
- Initial RPM Release.
