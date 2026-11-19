Name:		eisop-dataflow
Version:	4.4.0
Release:	1
Summary:	Dataflow framework from the Checker Framework
Group:		Development/Java
License:	GPLv2 with exceptions
URL:		https://github.com/typetools/checker-framework
# Checker Framework 4.4.0 dataflow sources. No prebuilt jars.
Source0:	dataflow-%{version}.tar.gz
# eisop tag checker-framework-3.41.0-eisop1. Error Prone requires this coordinate.
Source1:	eisop-dataflow-3.41.0.eisop1.tar.gz

%{!?plume_jar:%global plume_jar %{_javadir}/plume-util.jar}
%{!?reflection_jar:%global reflection_jar %{_javadir}/reflection-util.jar}
%{!?hashmap_jar:%global hashmap_jar %{_javadir}/hashmap-util.jar}
%{!?javacutil_jar:%global javacutil_jar %{_javadir}/javacutil.jar}
%{!?javacutil_old_jar:%global javacutil_old_jar %{_javadir}/javacutil-3.41.0.eisop1.jar}
%{!?javacparse_jar:%global javacparse_jar %{_javadir}/javac-parse.jar}

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(org.checkerframework:javacutil) = %{version}
BuildRequires:	mvn(org.checkerframework:javacutil) = 3.41.0-eisop1
BuildRequires:	mvn(org.checkerframework:checker-qual) = 4.4.0
BuildRequires:	mvn(org.checkerframework:checker-qual) = 3.41.0-eisop1
BuildRequires:	mvn(org.plumelib:plume-util) = 2.0.0
BuildRequires:	mvn(org.plumelib:reflection-util) = 2.0.0
BuildRequires:	mvn(org.plumelib:hashmap-util) = 2.0.0
BuildRequires:	mvn(org.plumelib:javac-parse) = 1.0.0
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
Requires:	mvn(org.checkerframework:javacutil) = %{version}
Requires:	mvn(org.checkerframework:javacutil) = 3.41.0-eisop1
Requires:	mvn(org.checkerframework:checker-qual) = 4.4.0
Requires:	mvn(org.checkerframework:checker-qual) = 3.41.0-eisop1
Requires:	mvn(org.plumelib:plume-util) = 2.0.0
Requires:	mvn(org.plumelib:reflection-util) = 2.0.0
Requires:	mvn(org.plumelib:hashmap-util) = 2.0.0
Requires:	mvn(org.plumelib:javac-parse) = 1.0.0
Requires:	mvn(com.google.guava:guava) = 33.6.0-jre

%description
org.checkerframework:dataflow %{version} is the typetools Checker
Framework dataflow jar. Error Prone still requires the eisop coordinate
3.41.0-eisop1, and that jar stays installed beside this one. %{version}
compiles against javacutil %{version}, checker-qual 4.4.0, plume-util
2.0.0, and javac-parse 1.0.0. The eisop jar compiles against the eisop
javacutil and qualifiers, and against plume-util 2.0.0.

%prep
%autosetup -N -n dataflow-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
test -f src/main/java/org/checkerframework/dataflow/cfg/builder/CFGBuilder.java
tar -C %{_builddir} -xf %{SOURCE1}
old=%{_builddir}/eisop-dataflow-3.41.0.eisop1
find "$old" -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries-old.list
if [ -s binaries-old.list ]; then
	cat binaries-old.list
	exit 1
fi
test -f "$old/src/main/java/org/checkerframework/dataflow/cfg/builder/CFGBuilder.java"

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
feature=$(java -XshowSettings:properties -version 2>&1 | awk -F= '/java.specification.version/{gsub(/ /,"",$2); print $2}')
major=$((feature + 44))
common="%{plume_jar}:%{reflection_jar}:%{hashmap_jar}:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar"
build_old() (
	cd "%{_builddir}/eisop-dataflow-3.41.0.eisop1"
	find src/main/java -name '*.java' > sources.list
	test "$(wc -l < sources.list)" -eq 173
	mkdir -p classes
	: > javac.args
	echo -encoding >> javac.args
	echo UTF-8 >> javac.args
	echo -proc:none >> javac.args
	echo -cp >> javac.args
	echo "%{javacutil_old_jar}:%{_javadir}/checker-qual-3.41.0-eisop1.jar:${common}" >> javac.args
	for p in api code comp file jvm main model parser processing resources tree util; do
		echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> javac.args
	done
	echo -d >> javac.args
	echo classes >> javac.args
	cat sources.list >> javac.args
	javac @javac.args
	jar cf dataflow.jar -C classes .
	jar i dataflow.jar
	jar tf dataflow.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
	javap -v -classpath dataflow.jar org.checkerframework.dataflow.cfg.builder.CFGBuilder | grep -F -q "major version: ${major}"
	cat > dataflow.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.checkerframework</groupId>
  <artifactId>dataflow</artifactId>
  <version>3.41.0-eisop1</version>
  <name>dataflow</name>
  <description>Dataflow framework from the eisop Checker Framework, built from source.</description>
  <url>https://github.com/eisop/checker-framework</url>
  <licenses>
    <license>
      <name>GPLv2 with exceptions</name>
      <url>http://www.gnu.org/software/classpath/license.html</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>javacutil</artifactId>
      <version>3.41.0-eisop1</version>
    </dependency>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>checker-qual</artifactId>
      <version>3.41.0-eisop1</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>plume-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>reflection-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>hashmap-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF
	grep -F -q '<version>3.41.0-eisop1</version>' dataflow.pom
)
build_new() (
	cd "%{_builddir}/dataflow-%{version}"
	find src/main/java -name '*.java' > sources.list
	test "$(wc -l < sources.list)" -eq 180
	mkdir -p classes
	: > javac.args
	echo -encoding >> javac.args
	echo UTF-8 >> javac.args
	echo -proc:none >> javac.args
	echo -cp >> javac.args
	echo "%{javacutil_jar}:%{_javadir}/checker-qual.jar:%{javacparse_jar}:${common}" >> javac.args
	for p in api code comp file jvm main model parser processing resources tree util; do
		echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> javac.args
	done
	echo -d >> javac.args
	echo classes >> javac.args
	cat sources.list >> javac.args
	javac @javac.args
	jar cf dataflow.jar -C classes .
	jar i dataflow.jar
	jar tf dataflow.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
	javap -v -classpath dataflow.jar org.checkerframework.dataflow.cfg.builder.CFGBuilder | grep -F -q "major version: ${major}"
	javap -public -classpath dataflow.jar org.checkerframework.dataflow.cfg.builder.CFGBuilder | grep -F -q 'build('
	cat > dataflow.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.checkerframework</groupId>
  <artifactId>dataflow</artifactId>
  <version>4.4.0</version>
  <name>dataflow</name>
  <description>Dataflow framework from the Checker Framework, built from source.</description>
  <url>https://github.com/typetools/checker-framework</url>
  <licenses>
    <license>
      <name>GPLv2 with exceptions</name>
      <url>http://www.gnu.org/software/classpath/license.html</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>javacutil</artifactId>
      <version>4.4.0</version>
    </dependency>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>checker-qual</artifactId>
      <version>4.4.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>plume-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>reflection-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>hashmap-util</artifactId>
      <version>2.0.0</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>javac-parse</artifactId>
      <version>1.0.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF
	grep -F -q '<version>4.4.0</version>' dataflow.pom
)
build_old
build_new

%install
set -eo pipefail
old="%{_builddir}/eisop-dataflow-3.41.0.eisop1"
sysjar install --buildroot %{buildroot} \
	--artifact "${old}/dataflow.pom:${old}/dataflow.jar" \
	--file-name dataflow-3.41.0.eisop1 \
	--filelist .mfiles-old
index="%{buildroot}/usr/share/sysjar/index/org.checkerframework/dataflow.sysjar"
test -f "$index"
/bin/mv "$index" "%{buildroot}/usr/share/sysjar/index/org.checkerframework/dataflow-3.41.0.eisop1.sysjar"
sed -i 's|/usr/share/sysjar/index/org\.checkerframework/dataflow\.sysjar|/usr/share/sysjar/index/org.checkerframework/dataflow-3.41.0.eisop1.sysjar|' .mfiles-old
idx="%{buildroot}/usr/share/sysjar/index/org.checkerframework/dataflow-3.41.0.eisop1.sysjar"
grep -F -q '"version": "3.41.0-eisop1"' "$idx"
grep -F -q '"artifactId": "dataflow"' "$idx"
new="%{_builddir}/dataflow-%{version}"
sysjar install --buildroot %{buildroot} \
	--artifact "${new}/dataflow.pom:${new}/dataflow.jar" \
	--file-name dataflow \
	--filelist .mfiles-new
idxn="%{buildroot}/usr/share/sysjar/index/org.checkerframework/dataflow.sysjar"
grep -F -q '"version": "%{version}"' "$idxn"
grep -F -q '"artifactId": "dataflow"' "$idxn"
test -s %{buildroot}%{_javadir}/dataflow-3.41.0.eisop1.jar
test -s %{buildroot}%{_javadir}/dataflow.jar
: > .mfiles
for list in .mfiles-old .mfiles-new
do
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
	done < "$list"
done
grep -F -q '/dataflow.jar' .mfiles
grep -F -q '/dataflow-3.41.0.eisop1.jar' .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check-new check-old
cat > Sample.java << 'END'
public class Sample {
	int branch(boolean flag) {
		if (flag) {
			return 1;
		} else {
			return 0;
		}
	}
}
END
cat > CheckDataflow.java << 'END'
import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.Tree;
import com.sun.source.util.JavacTask;
import com.sun.tools.javac.api.BasicJavacTask;
import com.sun.tools.javac.processing.JavacProcessingEnvironment;
import com.sun.tools.javac.util.Context;
import java.nio.file.Path;
import java.util.List;
import javax.annotation.processing.ProcessingEnvironment;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import org.checkerframework.dataflow.cfg.ControlFlowGraph;
import org.checkerframework.dataflow.cfg.builder.CFGBuilder;
import org.checkerframework.dataflow.cfg.node.Node;

public class CheckDataflow {
	public static void main(String[] args) throws Exception {
		JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
		StandardJavaFileManager fm = compiler.getStandardFileManager(null, null, null);
		Iterable<? extends JavaFileObject> files = fm.getJavaFileObjects(Path.of(args[0]));
		JavacTask task = (JavacTask) compiler.getTask(null, fm, null, List.of("--release", "8"), null, files);
		Iterable<? extends CompilationUnitTree> units = task.parse();
		task.analyze();
		CompilationUnitTree root = units.iterator().next();
		ClassTree cls = (ClassTree) root.getTypeDecls().get(0);
		MethodTree method = null;
		for (Tree member : cls.getMembers()) {
			if (member instanceof MethodTree) {
				MethodTree mt = (MethodTree) member;
				if (mt.getName().contentEquals("branch")) {
					method = mt;
				}
			}
		}
		if (method == null) {
			throw new RuntimeException("no branch");
		}
		Context ctx = ((BasicJavacTask) task).getContext();
		ProcessingEnvironment env = JavacProcessingEnvironment.instance(ctx);
		ControlFlowGraph cfg = CFGBuilder.build(root, method, cls, env);
		List<Node> nodes = cfg.getAllNodes();
		int returns = 0;
		for (Node n : nodes) {
			if (n.getClass().getSimpleName().equals("ReturnNode")) {
				returns++;
			}
		}
		if (nodes.size() != 5 || returns != 2) {
			throw new RuntimeException("cfg " + nodes.size() + " " + returns);
		}
		System.out.println("dataflow_ok " + args[1] + " " + nodes.size() + " " + returns);
	}
}
END
: > check.args
echo -encoding >> check.args
echo UTF-8 >> check.args
echo -proc:none >> check.args
for p in api code comp file jvm main model parser processing resources tree util; do
	echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> check.args
done
: > java.args
for p in api code comp file jvm main model parser processing resources tree util; do
	echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> java.args
	echo "--add-opens=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> java.args
done
common="%{plume_jar}:%{reflection_jar}:%{hashmap_jar}:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar"
run_check() {
	label="$1"
	df="$2"
	ju="$3"
	qual="$4"
	extra="$5"
	outdir="$6"
	cp="$df:$ju:$qual:$common:$extra"
	mkdir -p "$outdir"
	javac @check.args -cp "$cp" -d "$outdir" CheckDataflow.java
	java @java.args -cp "$outdir:$cp" CheckDataflow Sample.java "$label" > "$outdir/out.txt"
	cat "$outdir/out.txt"
	grep -F -q "dataflow_ok ${label} 5 2" "$outdir/out.txt"
}
run_check %{version} %{buildroot}%{_javadir}/dataflow.jar %{javacutil_jar} %{_javadir}/checker-qual.jar %{javacparse_jar} check-new
run_check 3.41.0-eisop1 %{buildroot}%{_javadir}/dataflow-3.41.0.eisop1.jar %{javacutil_old_jar} %{_javadir}/checker-qual-3.41.0-eisop1.jar %{_javadir}/checker-qual-3.41.0-eisop1.jar check-old

%files -f .mfiles
%license LICENSE.txt
