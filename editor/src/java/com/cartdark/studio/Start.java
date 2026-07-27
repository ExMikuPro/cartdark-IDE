// Copyright 2026 ExMikuPro
// Licensed under the Defold License version 1.0.

package com.cartdark.studio;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.stage.Stage;

/**
 * CartDark Studio's JavaFX lifecycle. This deliberately does not initialize
 * Defold's resource unpacker, GL profile, engine, updater, or target discovery.
 */
public final class Start extends Application {
    private StudioApplication studioApplication;

    @Override
    public void start(Stage primaryStage) {
        Thread loader = new Thread(() -> {
            try {
                studioApplication = new StudioApplication(Thread.currentThread().getContextClassLoader());
                studioApplication.waitForClojureNamespaces();
                String[] args = getParameters().getRaw().toArray(String[]::new);
                Platform.runLater(() -> studioApplication.run(args));
            } catch (Throwable throwable) {
                throwable.printStackTrace();
                Platform.runLater(() -> {
                    throw new IllegalStateException("Unable to start CartDark Studio", throwable);
                });
            }
        }, "cartdark-clojure-loader");
        loader.setDaemon(true);
        loader.start();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
