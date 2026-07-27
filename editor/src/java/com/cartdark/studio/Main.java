// Copyright 2026 ExMikuPro
// Licensed under the Defold License version 1.0.

package com.cartdark.studio;

/**
 * Non-JavaFX launcher used to avoid the Java launcher module-path heuristic.
 */
public final class Main {
    private Main() {
    }

    public static void main(String[] args) {
        Start.main(args);
    }
}
