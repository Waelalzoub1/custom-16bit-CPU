// Simulate a .dig CPU in Digital's own engine (headless): load a program into the
// program RAM, clock it, and dump the register file and a memory window.
//   javac -cp Digital.jar DigSim.java
//   java  -cp Digital.jar:. DigSim CPU.dig program.hex maxCycles memLo memHi
// Halt is detected as the program counter (RAM port 2 address) not changing for 8 cycles.
import de.neemann.digital.cli.CircuitLoader;
import de.neemann.digital.core.*;
import de.neemann.digital.core.memory.*;
import de.neemann.digital.core.wiring.Clock;
import java.lang.reflect.Field;
import java.nio.file.*;
import java.util.*;

public class DigSim {
    public static void main(String[] a) throws Exception {
        Model m = new CircuitLoader(a[0]).createModel();
        int maxCycles = Integer.parseInt(a[2]), lo = Integer.parseInt(a[3]), hi = Integer.parseInt(a[4]);
        RAMDualAccess ram = m.findNode(RAMDualAccess.class).get(0);
        RegisterFile rf = m.findNode(RegisterFile.class).get(0);
        List<String> lines = Files.readAllLines(Paths.get(a[1]));
        m.init();
        DataField mem = ram.getMemory();
        int addr = 0;
        for (String l : lines) { l = l.trim(); if (l.isEmpty() || l.startsWith("v2.0")) continue; mem.setData(addr++, Long.parseLong(l, 16)); }
        Field f = RAMDualAccess.class.getDeclaredField("addr2In"); f.setAccessible(true);
        ObservableValue pc = (ObservableValue) f.get(ram);
        ObservableValue clk = m.getClocks().get(0).getClockOutput();
        for (Signal s : m.getInputs()) if (s.getName().equals("R")) {           // external reset pulse
            final ObservableValue r = s.getValue();
            m.modify(() -> r.setBool(true));  tick(m, clk); tick(m, clk);  m.modify(() -> r.setBool(false));
        }
        long last = -1; int same = 0, cycles = 0; boolean halted = false;
        for (; cycles < maxCycles; cycles++) {
            tick(m, clk);
            long p = pc.getValue();
            same = (p == last) ? same + 1 : 0; last = p;
            if (same >= 8) { halted = true; break; }
        }
        System.out.println("PC " + pc.getValue());
        System.out.println("CYCLES " + cycles);
        System.out.println("HALTED " + (halted ? 1 : 0));
        for (int i = 0; i < 16; i++) System.out.println("R" + i + " " + rf.getMemory().getDataWord(i));
        for (int i = lo; i < hi; i++) System.out.println("MEM " + i + " " + mem.getDataWord(i));
        m.close();
    }
    static void tick(Model m, ObservableValue clk) {
        m.modify(() -> clk.setBool(true));
        m.modify(() -> clk.setBool(false));
    }
}
