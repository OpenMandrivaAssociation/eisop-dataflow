%global mvnver 3.41.0-eisop1

Name:		eisop-dataflow
Version:	3.41.0.eisop1
Release:	1
Summary:	Dataflow framework from the eisop Checker Framework
Group:		Development/Java
License:	GPLv2 with exceptions
URL:		https://github.com/eisop/checker-framework
# Tag checker-framework-3.41.0-eisop1, dataflow main sources and the
# upstream license only. Tests and prebuilt jars are omitted.
Source0:	eisop-dataflow-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(org.checkerframework:javacutil) = %{mvnver}
BuildRequires:	mvn(org.checkerframework:checker-qual) = %{mvnver}
BuildRequires:	mvn(org.plumelib:plume-util) = 1.8.1
BuildRequires:	mvn(org.plumelib:reflection-util) = 1.0.6
BuildRequires:	mvn(org.plumelib:hashmap-util) = 0.0.1
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
Requires:	mvn(org.checkerframework:javacutil) = %{mvnver}
Requires:	mvn(org.checkerframework:checker-qual) = %{mvnver}
Requires:	mvn(org.plumelib:plume-util) = 1.8.1
Requires:	mvn(org.plumelib:reflection-util) = 1.0.6
Requires:	mvn(com.google.guava:guava) = 33.6.0-jre

%description
org.checkerframework:dataflow %{mvnver}. Control-flow graph and dataflow
analysis from the eisop Checker Framework, compiled from source against
the system javacutil, plume-util, and checker-qual jars. This is the
unshaded jar. error-prone upstream depends on a shaded rename of these
packages; that rename is applied when error-prone itself is built.

%prep
%autosetup -n eisop-dataflow-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
find src/main/java -name '*.java' > sources.list
test "$(wc -l < sources.list)" -eq 173
mkdir -p classes
: > javac.args
echo -encoding >> javac.args
echo UTF-8 >> javac.args
echo -proc:none >> javac.args
echo -cp >> javac.args
echo "%{_javadir}/javacutil.jar:%{_javadir}/checker-qual-%{mvnver}.jar:%{_javadir}/plume-util.jar:%{_javadir}/reflection-util.jar:%{_javadir}/hashmap-util.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar" >> javac.args
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
feature=$(java -XshowSettings:properties -version 2>&1 | awk -F= '/java.specification.version/{gsub(/ /,"",$2); print $2}')
major=$((feature + 44))
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
      <version>1.8.1</version>
    </dependency>
    <dependency>
      <groupId>org.plumelib</groupId>
      <artifactId>reflection-util</artifactId>
      <version>1.0.6</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check-classes
CP="dataflow.jar:%{_javadir}/javacutil.jar:%{_javadir}/checker-qual-%{mvnver}.jar:%{_javadir}/plume-util.jar:%{_javadir}/reflection-util.jar:%{_javadir}/hashmap-util.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar"
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
		System.out.println("dataflow_ok " + nodes.size() + " " + returns);
		if (nodes.size() < 2 || returns < 2) {
			throw new RuntimeException("cfg too small");
		}
	}
}
END
: > check.args
echo -encoding >> check.args
echo UTF-8 >> check.args
echo -proc:none >> check.args
echo -cp >> check.args
echo "$CP" >> check.args
for p in api code comp file jvm main model parser processing resources tree util; do
	echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> check.args
done
echo -d >> check.args
echo check-classes >> check.args
echo CheckDataflow.java >> check.args
javac @check.args
: > java.args
for p in api code comp file jvm main model parser processing resources tree util; do
	echo "--add-exports=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> java.args
	echo "--add-opens=jdk.compiler/com.sun.tools.javac.${p}=ALL-UNNAMED" >> java.args
done
echo -cp >> java.args
echo "check-classes:$CP" >> java.args
echo CheckDataflow >> java.args
echo Sample.java >> java.args
java @java.args > check.log
cat check.log
grep -F -q 'dataflow_ok 5 2' check.log

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact dataflow.pom:dataflow.jar \
	--file-name dataflow \
	--filelist .mfiles

%files -f .mfiles
%license LICENSE.txt
