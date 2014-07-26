Name:           node
Version:        v0.10.29
Release:        1%{?dist}
Summary:        Node.js

Group:          C
License:        BSD
URL:            http://nodejs.org
Source0:        http://nodejs.org/dist/v0.10.29/%{name}-%{version}.tar.gz

BuildRequires:  gcc, gcc-c++

%define         _topdir   /home/stephane/work/packages/%{name}.rpmbuild
%define         node_dir  /usr/local/%{name}

%description


%prep
%setup -q


%build
./configure --prefix=%{node_dir}
make %{?_smp_mflags}

%check
#make test

%install
%{__rm} -rf %{buildroot}
make install DESTDIR=%{buildroot}

%post
cd %{_bindir}; ln -s %{node_dir}/bin/npm

%preun
if [ $1 = 0 ]; then
  rm -f %{_bindir}/npm
fi


%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc
%{node_dir}/*


%changelog
* Fri Jul 25 2014 Stephane Peiry <stephane@pittypanda.com> 2.8.13-1.0
- Initial RPM Release.
