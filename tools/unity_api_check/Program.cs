// Lists every Unity API (type and member) the project's scripts use, resolved by Roslyn against Unity reference assemblies:
// one line per use, "Type.Member<TAB>file:line<TAB>full signature<TAB>namespace". With WARNINGS=1 it lists the compiler's
// warnings instead. Used by run.sh (README.md there).
//   dotnet apiscan.dll <Assets dir> <UnityEngine.dll;UnityEditor.dll> <stubs dir> <defines; separated>
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

var project = args[0]; var refs = args[1].Split(';'); var stubs = args[2]; var defines = args[3].Split(';');
var opts = new CSharpParseOptions(LanguageVersion.CSharp9, preprocessorSymbols: defines);
var files = Directory.GetFiles(project, "*.cs", SearchOption.AllDirectories).Concat(Directory.GetFiles(stubs, "*.cs")).ToList();
var trees = files.Select(f => CSharpSyntaxTree.ParseText(File.ReadAllText(f), opts, f)).ToList();
var netRefs = ((string)AppContext.GetData("TRUSTED_PLATFORM_ASSEMBLIES")).Split(Path.PathSeparator)
    .Where(p => Path.GetFileName(p).StartsWith("System") || Path.GetFileName(p) == "mscorlib.dll" || Path.GetFileName(p) == "netstandard.dll")
    .Select(p => MetadataReference.CreateFromFile(p));
var comp = CSharpCompilation.Create("scan", trees, netRefs.Concat(refs.Select(r => MetadataReference.CreateFromFile(r))),
    new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary, allowUnsafe: true));
if (Environment.GetEnvironmentVariable("WARNINGS") == "1")
{
    foreach (var d in comp.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Warning && !d.Location.SourceTree.FilePath.StartsWith(stubs)))
        Console.WriteLine($"{d.Id}\t{Path.GetRelativePath(project, d.Location.SourceTree.FilePath)}:{d.Location.GetLineSpan().StartLinePosition.Line + 1}\t{d.GetMessage()}");
    return;
}
var seen = new HashSet<string>();
foreach (var tree in trees)
{
    if (tree.FilePath.StartsWith(stubs)) continue;
    var model = comp.GetSemanticModel(tree);
    foreach (var node in tree.GetRoot().DescendantNodes())
    {
        if (node is not (IdentifierNameSyntax or GenericNameSyntax)) continue;
        var info = model.GetSymbolInfo(node);
        var sym = info.Symbol ?? info.CandidateSymbols.FirstOrDefault();
        if (sym == null) continue;
        var asm = sym.ContainingAssembly?.Name ?? (sym as ITypeSymbol)?.ContainingAssembly?.Name;
        if (asm == null || !(asm.StartsWith("UnityEngine") || asm.StartsWith("UnityEditor"))) continue;
        string type, member;
        if (sym is INamedTypeSymbol t) { type = t.Name; member = t.Name; }
        else { type = sym.ContainingType?.Name ?? "?"; member = sym.Name; if (sym is IMethodSymbol m && m.MethodKind == MethodKind.Constructor) member = type; }
        var line = tree.GetLineSpan(node.Span).StartLinePosition.Line + 1;
        Console.WriteLine($"{type}.{member}\t{Path.GetRelativePath(project, tree.FilePath)}:{line}\t{sym.ToDisplayString()}\t{sym.ContainingNamespace?.ToDisplayString()}");
    }
}
