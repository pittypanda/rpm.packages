Name:           nginx
Version:        1.7.3
Release:        5%{?dist}
Summary:        Nginx Web Server

Group:          Nginx Web Server
License:        BSD
URL:            http://nginx.org
Source0:        http://nginx.org/download/%{name}-%{version}.tar.gz

BuildRequires:  gcc, pcre-devel, zlib-devel, openssl-devel
Requires:       pcre, openssl

%define         _topdir    %{getenv:HOME}/work/packages/%{name}.rpmbuild
%define         pid_file   %{_localstatedir}/run/%{name}.pid
%define         nginx_dir  /usr/local/%{name}

%description


%prep
%setup -q

%{__cat} <<EOF >%{name}.logrotate
%{nginx_dir}/logs/*log {
    missingok
}
EOF

%{__cat} <<'EOF' >%{name}.sysv
#!/bin/sh
#
# nginx - this script starts and stops the nginx daemon
#
# chkconfig:   - 85 15 
# description: Nginx is an HTTP(S) server and HTTP(S) reverse proxy
# processname: %{name}
# config:      %{_sysconfdir}/%{name}.conf
# pidfile:     %{pid_file}
 
# Source function library.
. /etc/rc.d/init.d/functions
 
# Source networking configuration.
. /etc/sysconfig/network
 
# Check that networking is up.
[ "$NETWORKING" = "no" ] && exit 0
 
nginx="%{nginx_dir}/sbin/nginx"
prog=$(basename $nginx)
 
NGINX_CONF_FILE="%{_sysconfdir}/%{name}.conf"
 
[ -f /etc/sysconfig/nginx ] && . /etc/sysconfig/nginx
 
lockfile=/var/lock/subsys/nginx
 
start() {
    [ -x $nginx ] || exit 5
    [ -f $NGINX_CONF_FILE ] || exit 6
    echo -n $"Starting $prog: "
    daemon $nginx -c $NGINX_CONF_FILE
    retval=$?
    echo
    [ $retval -eq 0 ] && touch $lockfile
    return $retval
}
 
stop() {
    echo -n $"Stopping $prog: "
    killproc $prog -QUIT
    retval=$?
    echo
    [ $retval -eq 0 ] && rm -f $lockfile
    return $retval
}
 
restart() {
    configtest || return $?
    stop
    sleep 1
    start
}
 
reload() {
    configtest || return $?
    echo -n $"Reloading $prog: "
    killproc $nginx -HUP
    RETVAL=$?
    echo
}
 
force_reload() {
    restart
}
 
configtest() {
  $nginx -t -c $NGINX_CONF_FILE
}
 
rh_status() {
    status $prog
}
 
rh_status_q() {
    rh_status >/dev/null 2>&1
}
 
case "$1" in
    start)
        rh_status_q && exit 0
        $1
        ;;
    stop)
        rh_status_q || exit 0
        $1
        ;;
    restart|configtest)
        $1
        ;;
    reload)
        rh_status_q || exit 7
        $1
        ;;
    force-reload)
        force_reload
        ;;
    status)
        rh_status
        ;;
    condrestart|try-restart)
        rh_status_q || exit 0
            ;;
    *)
        echo $"Usage: $0 {start|stop|status|restart|condrestart|try-restart|reload|force-reload|configtest}"
        exit 2
esac
EOF


%build
./configure --prefix=%{nginx_dir} --http-client-body-temp-path=%{nginx_dir}/work/client_body_temp --http-proxy-temp-path=%{nginx_dir}/work/proxy_temp --http-fastcgi-temp-path=%{nginx_dir}/work/fastcgi_temp --http-uwsgi-temp-path=%{nginx_dir}/work/uwsgi_temp --http-scgi-temp-path=%{nginx_dir}/work/scgi_temp
make %{?_smp_mflags}

cp conf/nginx.conf conf/nginx.conf.ori
sed -e "s/^#user .*/user %{name};/" -e "s:^#pid .*:pid %{pid_file};:" conf/nginx.conf.ori > conf/nginx.conf


%check
#make test

%install
%{__rm} -rf %{buildroot}
make install DESTDIR=%{buildroot}

%{__install} -Dp -m 0755 %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -Dp -m 0755 %{name}.sysv %{buildroot}%{_sysconfdir}/init.d/%{name}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_dir}/work

#%{__mv} %{buildroot}%{nginx_dir}/conf/nginx.conf %{buildroot}%{_sysconfdir}/%{name}.conf
mv %{buildroot}%{nginx_dir}/conf/nginx.conf %{buildroot}%{_sysconfdir}/%{name}.conf


%pre
getent group  %{name} &> /dev/null || groupadd -r %{name} &> /dev/null
getent passwd %{name} &> /dev/null || \
  useradd -r -s /sbin/nologin -d %{nginx_dir} -c '%{name} web server' -g %{name} %{name} &> /dev/null
exit 0

%post
/sbin/chkconfig --add %{name}
cd %{nginx_dir}/conf; ln -s %{_sysconfdir}/%{name}.conf

%preun
if [ $1 = 0 ]; then
  /sbin/service %{name} stop > /dev/null 2>&1
  /sbin/chkconfig --del %{name}

  if [ -h "%{nginx_dir}/conf/%{name}.conf" ]; then
    rm -f %{nginx_dir}/conf/%{name}.conf
  fi
fi


%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-,%{name},%{name},-)
%doc
%dir %attr(0755,%{name},%{name}) %{nginx_dir}
%{nginx_dir}/*
%{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %attr(0644,root,root) %{_sysconfdir}/%{name}.conf
%attr(0755,root,root) %{_sysconfdir}/init.d/%{name}


%changelog
* Mon Jul 24 2014 Stephane Peiry <stephane@pittypanda.com> 2.8.13-1.0
- Initial RPM Release.
