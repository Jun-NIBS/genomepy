import os
import pytest
import re
from subprocess import check_call
from tempfile import mkdtemp
from shutil import rmtree, copyfile

from genomepy.plugin import init_plugins, activate
from genomepy.utils import cmd_ok
from genomepy.functions import Genome
from genomepy.plugins.bwa import BwaPlugin
from genomepy.plugins.gmap import GmapPlugin
from genomepy.plugins.minimap2 import Minimap2Plugin
from genomepy.plugins.bowtie2 import Bowtie2Plugin
from genomepy.plugins.hisat2 import Hisat2Plugin
from genomepy.plugins.blacklist import BlacklistPlugin


@pytest.fixture(scope="module")
def tempdir():
    """Temporary directory."""
    tmpdir = mkdtemp()
    yield tmpdir
    rmtree(tmpdir)


@pytest.fixture(scope="module", params=["unzipped", "bgzipped"])
def genome(request, tempdir):
    """Create a test genome."""
    name = "dm3"  # Use fake name for blacklist test
    fafile = "tests/data/small_genome.fa"

    # Input needs to be bgzipped, depending on param
    if os.path.exists(fafile + ".gz"):
        if request.param == "unzipped":
            check_call(["gunzip", fafile + ".gz"])
    elif request.param == "bgzipped":
        check_call(["bgzip", fafile])

    tmpdir = os.path.join(tempdir, request.param, name)
    os.makedirs(tmpdir)

    if request.param == "bgzipped":
        fafile += ".gz"

    copyfile(fafile, os.path.join(tmpdir, os.path.basename(fafile)))
    for p in init_plugins():
        activate(p)
    # provide the fixture value
    yield Genome(name, genome_dir=os.path.join(tempdir, request.param))
    if os.path.exists(fafile) and request.param == "unzipped":
        check_call(["bgzip", fafile])


def test_blacklist(genome):
    """Create bwa index."""
    assert os.path.exists(genome.filename)

    p = BlacklistPlugin()
    p.after_genome_download(genome)
    fname = re.sub(".fa(.gz)?$", ".blacklist.bed.gz", genome.filename)
    assert os.path.exists(fname)


def test_bwa(genome):
    """Create bwa index."""
    assert os.path.exists(genome.filename)

    if cmd_ok("bwa"):
        p = BwaPlugin()
        p.after_genome_download(genome)
        dirname = os.path.dirname(genome.filename)
        index_dir = os.path.join(dirname, "index", "bwa")
        assert os.path.exists(index_dir)
        assert os.path.exists(os.path.join(index_dir, "{}.fa.sa".format(genome.name)))


def test_minimap2(genome):
    """Create minimap2 index."""
    assert os.path.exists(genome.filename)
    if cmd_ok("minimap2"):
        p = Minimap2Plugin()
        p.after_genome_download(genome)
        dirname = os.path.dirname(genome.filename)
        index_dir = os.path.join(dirname, "index", "minimap2")
        assert os.path.exists(index_dir)
        assert os.path.exists(os.path.join(index_dir, "{}.mmi".format(genome.name)))


def test_bowtie2(genome):
    """Create bbowtie2 index."""
    assert os.path.exists(genome.filename)
    if cmd_ok("bowtie2"):
        p = Bowtie2Plugin()
        p.after_genome_download(genome)
        dirname = os.path.dirname(genome.filename)
        index_dir = os.path.join(dirname, "index", "bowtie2")
        assert os.path.exists(index_dir)
        assert os.path.exists(os.path.join(index_dir, "{}.1.bt2".format(genome.name)))


def test_hisat2(genome):
    """Create hisat2 index."""
    assert os.path.exists(genome.filename)
    if cmd_ok("hisat2-build"):
        p = Hisat2Plugin()
        p.after_genome_download(genome)
        dirname = os.path.dirname(genome.filename)
        index_dir = os.path.join(dirname, "index", "hisat2")
        assert os.path.exists(index_dir)
        assert os.path.exists(os.path.join(index_dir, "{}.1.ht2".format(genome.name)))


def test_gmap(genome):
    """Create gmap index."""
    assert os.path.exists(genome.filename)
    if cmd_ok("gmap"):
        p = GmapPlugin()
        p.after_genome_download(genome)
        dirname = os.path.dirname(genome.filename)
        index_dir = os.path.join(dirname, "index", "gmap", genome.name)
        assert os.path.exists(index_dir)
        assert os.path.exists(os.path.join(index_dir, "{}.version".format(genome.name)))
