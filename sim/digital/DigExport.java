// Headless Verilog export of a .dig circuit with Digital's own generator.
//   javac -cp Digital.jar DigExport.java
//   java  -cp Digital.jar:. DigExport CPU_export.dig CPU_export.v
import de.neemann.digital.cli.CircuitLoader;
import de.neemann.digital.hdl.printer.CodePrinter;
import de.neemann.digital.hdl.verilog2.VerilogGenerator;
import java.io.File;

public class DigExport {
    public static void main(String[] a) throws Exception {
        CircuitLoader cl = new CircuitLoader(a[0]);
        try (VerilogGenerator gen = new VerilogGenerator(cl.getLibrary(), new CodePrinter(new File(a[1])))) {
            gen.export(cl.getCircuit());
        }
        System.out.println("wrote " + a[1]);
    }
}
