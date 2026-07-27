// Copyright 2026 ExMikuPro
// Licensed under the Defold License version 1.0.

package com.cartdark.studio;

import org.projectodd.shimdandy.ClojureRuntimeShim;

/**
 * Isolated Clojure runtime for the CartDark entry point.
 */
public final class StudioApplication {
    private final ClojureRuntimeShim runtime;

    public StudioApplication(ClassLoader classLoader) {
        runtime = ClojureRuntimeShim.newRuntime(classLoader, "cartdark");
        runtime.invoke("cartdark.bootloader/load-boot");
    }

    public void waitForClojureNamespaces() {
        runtime.invoke("cartdark.bootloader/wait-until-boot-loaded");
    }

    public void run(String[] args) {
        runtime.invoke("cartdark.bootloader/main", args);
    }
}
