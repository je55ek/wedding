WORKDIR=`pwd`
BUILDDIR="${WORKDIR}/build"
mkdir -p "${BUILDDIR}"
pip install "${WORKDIR}/../" -t "${BUILDDIR}" --no-compile
cp "${WORKDIR}/app.py" "${BUILDDIR}/"
pushd "${BUILDDIR}"
rm -r *.egg-info
rm -r *.dist-info
zip -r wedding-app.zip ./*
popd
mv "${BUILDDIR}/wedding-app.zip" .
