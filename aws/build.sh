WORKDIR=`pwd`
BUILDDIR="${WORKDIR}/build"
VERSION=`git describe --long --dirty`
ZIPNAME="wedding-app-${VERSION}.zip"
rm -rf "${BUILDDIR}"
mkdir "${BUILDDIR}"
pip install "${WORKDIR}/../" -t "${BUILDDIR}" --no-compile
cp "${WORKDIR}/app.py" "${BUILDDIR}/"
pushd "${BUILDDIR}"
rm -r *.egg-info
rm -r *.dist-info
zip -r "${ZIPNAME}" ./*
popd
mv "${BUILDDIR}/${ZIPNAME}" .
