// Digest: 74a9df3c733e0d62340921c150349bfbaae7c87d
/* eslint-disable */
/* tslint:disable */
/**
 * This file was automatically generated by json-schema-to-typescript.
 * DO NOT MODIFY IT BY HAND. Instead, modify the source JSONSchema file,
 * and run json-schema-to-typescript to regenerate this file.
 */

export interface Types {
  DjangoDefaultProps: ServerTemplatesDjangoDefault;
  globals: {};
  Context: ReactivatedSerializationContextProcessorsBaseContext &
    ReactivatedSerializationContextProcessorsMessagesProcessor &
    ReactivatedSerializationContextProcessorsRequestProcessor &
    ReactivatedSerializationContextProcessorsCSRFProcessor;
}
export interface ServerTemplatesDjangoDefault {
  version: string;
  form: ServerTemplatesFoo;
}
export interface ServerTemplatesFoo {
  name: "server.templates.Foo";
  errors: {} | null;
  fields: {};
  prefix: string;
  iterator: [];
}
export interface ReactivatedSerializationContextProcessorsBaseContext {
  template_name: string;
}
export interface ReactivatedSerializationContextProcessorsMessagesProcessor {
  messages: ReactivatedSerializationContextProcessorsMessage[];
}
export interface ReactivatedSerializationContextProcessorsMessage {
  level_tag: "info" | "success" | "error" | "warning" | "debug";
  message: string;
  level: number;
  from_server: boolean;
}
export interface ReactivatedSerializationContextProcessorsRequestProcessor {
  request: ReactivatedSerializationContextProcessorsRequest;
}
export interface ReactivatedSerializationContextProcessorsRequest {
  path: string;
  url: string;
}
export interface ReactivatedSerializationContextProcessorsCSRFProcessor {
  csrf_token: string;
}
import React from "react"
import createContext from "reactivated/context";
import * as forms from "reactivated/forms";

// Note: this needs strict function types to behave correctly with excess properties etc.
export type Checker<P, U extends (React.FunctionComponent<P> | React.ComponentClass<P>)> = {};

export const {Context, Provider, getServerData} = createContext<Types["Context"]>();

export const getTemplate = ({template_name}: {template_name: string}) => {
    // This require needs to be *inside* the function to avoid circular dependencies with esbuild.
    const { default: templates, filenames } = require('../templates/**/*');
    const templatePath = "../templates/" + template_name + ".tsx";
    const Template: React.ComponentType<any> = templates.find((t: any, index: number) => filenames[index] === templatePath).default;
    return Template;
}

export const CSRFToken = forms.createCSRFToken(Context);

export const {createRenderer, Iterator} = forms.bindWidgetType<Types["globals"]["Widget"]>();


import DjangoDefaultImplementation from "@client/templates/DjangoDefault"
export type DjangoDefaultCheck = Checker<Types["DjangoDefaultProps"], typeof DjangoDefaultImplementation>;


        
