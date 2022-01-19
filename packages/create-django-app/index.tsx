#!/usr/bin/env node
import fs from "fs";
import path from "path";
import child_process from "child_process";

const cleanup = () => {
    console.log("Cleaning up.");
};

const handleExit = () => {
    cleanup();
    console.log("Exiting without error.");
    process.exit();
};

const handleError = (e: unknown) => {
    console.error("ERROR! An error was encountered while executing");
    console.error(e);
    cleanup();
    console.log("Exiting with error.");
    process.exit(1);
};

process.on("SIGINT", handleExit);
process.on("uncaughtException", handleError);

try {
    const nixStatus = child_process.execSync(`nix --version`, {stdio: "ignore"});
} catch (error) {
    console.log(
        "You need to install nix. Visit https://nixos.org/download.html to get started",
    );
    throw error;
}
