/*eslint-disable block-scoped-var, id-length, no-control-regex, no-magic-numbers, no-prototype-builtins, no-redeclare, no-shadow, no-var, sort-vars*/
"use strict";

var $protobuf = require("protobufjs/minimal");

// Common aliases
var $Reader = $protobuf.Reader, $Writer = $protobuf.Writer, $util = $protobuf.util;

// Exported root namespace
var $root = $protobuf.roots["default"] || ($protobuf.roots["default"] = {});

$root.Header = (function() {

    /**
     * Properties of a Header.
     * @exports IHeader
     * @interface IHeader
     * @property {number|null} [university] Header university
     * @property {number|null} [institute] Header institute
     * @property {number|null} [branch] Header branch
     * @property {number|null} [schema] Header schema
     */

    /**
     * Constructs a new Header.
     * @exports Header
     * @classdesc Represents a Header.
     * @implements IHeader
     * @constructor
     * @param {IHeader=} [properties] Properties to set
     */
    function Header(properties) {
        if (properties)
            for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                if (properties[keys[i]] != null)
                    this[keys[i]] = properties[keys[i]];
    }

    /**
     * Header university.
     * @member {number} university
     * @memberof Header
     * @instance
     */
    Header.prototype.university = 0;

    /**
     * Header institute.
     * @member {number} institute
     * @memberof Header
     * @instance
     */
    Header.prototype.institute = 0;

    /**
     * Header branch.
     * @member {number} branch
     * @memberof Header
     * @instance
     */
    Header.prototype.branch = 0;

    /**
     * Header schema.
     * @member {number} schema
     * @memberof Header
     * @instance
     */
    Header.prototype.schema = 0;

    /**
     * Creates a new Header instance using the specified properties.
     * @function create
     * @memberof Header
     * @static
     * @param {IHeader=} [properties] Properties to set
     * @returns {Header} Header instance
     */
    Header.create = function create(properties) {
        return new Header(properties);
    };

    /**
     * Encodes the specified Header message. Does not implicitly {@link Header.verify|verify} messages.
     * @function encode
     * @memberof Header
     * @static
     * @param {IHeader} message Header message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Header.encode = function encode(message, writer) {
        if (!writer)
            writer = $Writer.create();
        if (message.university != null && Object.hasOwnProperty.call(message, "university"))
            writer.uint32(/* id 1, wireType 0 =*/8).int32(message.university);
        if (message.institute != null && Object.hasOwnProperty.call(message, "institute"))
            writer.uint32(/* id 2, wireType 0 =*/16).int32(message.institute);
        if (message.branch != null && Object.hasOwnProperty.call(message, "branch"))
            writer.uint32(/* id 3, wireType 0 =*/24).int32(message.branch);
        if (message.schema != null && Object.hasOwnProperty.call(message, "schema"))
            writer.uint32(/* id 4, wireType 0 =*/32).int32(message.schema);
        return writer;
    };

    /**
     * Encodes the specified Header message, length delimited. Does not implicitly {@link Header.verify|verify} messages.
     * @function encodeDelimited
     * @memberof Header
     * @static
     * @param {IHeader} message Header message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Header.encodeDelimited = function encodeDelimited(message, writer) {
        return this.encode(message, writer).ldelim();
    };

    /**
     * Decodes a Header message from the specified reader or buffer.
     * @function decode
     * @memberof Header
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @param {number} [length] Message length if known beforehand
     * @returns {Header} Header
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Header.decode = function decode(reader, length, error) {
        if (!(reader instanceof $Reader))
            reader = $Reader.create(reader);
        var end = length === undefined ? reader.len : reader.pos + length, message = new $root.Header();
        while (reader.pos < end) {
            var tag = reader.uint32();
            if (tag === error)
                break;
            switch (tag >>> 3) {
            case 1: {
                    message.university = reader.int32();
                    break;
                }
            case 2: {
                    message.institute = reader.int32();
                    break;
                }
            case 3: {
                    message.branch = reader.int32();
                    break;
                }
            case 4: {
                    message.schema = reader.int32();
                    break;
                }
            default:
                reader.skipType(tag & 7);
                break;
            }
        }
        return message;
    };

    /**
     * Decodes a Header message from the specified reader or buffer, length delimited.
     * @function decodeDelimited
     * @memberof Header
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @returns {Header} Header
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Header.decodeDelimited = function decodeDelimited(reader) {
        if (!(reader instanceof $Reader))
            reader = new $Reader(reader);
        return this.decode(reader, reader.uint32());
    };

    /**
     * Verifies a Header message.
     * @function verify
     * @memberof Header
     * @static
     * @param {Object.<string,*>} message Plain object to verify
     * @returns {string|null} `null` if valid, otherwise the reason why it is not
     */
    Header.verify = function verify(message) {
        if (typeof message !== "object" || message === null)
            return "object expected";
        if (message.university != null && message.hasOwnProperty("university"))
            if (!$util.isInteger(message.university))
                return "university: integer expected";
        if (message.institute != null && message.hasOwnProperty("institute"))
            if (!$util.isInteger(message.institute))
                return "institute: integer expected";
        if (message.branch != null && message.hasOwnProperty("branch"))
            if (!$util.isInteger(message.branch))
                return "branch: integer expected";
        if (message.schema != null && message.hasOwnProperty("schema"))
            if (!$util.isInteger(message.schema))
                return "schema: integer expected";
        return null;
    };

    /**
     * Creates a Header message from a plain object. Also converts values to their respective internal types.
     * @function fromObject
     * @memberof Header
     * @static
     * @param {Object.<string,*>} object Plain object
     * @returns {Header} Header
     */
    Header.fromObject = function fromObject(object) {
        if (object instanceof $root.Header)
            return object;
        var message = new $root.Header();
        if (object.university != null)
            message.university = object.university | 0;
        if (object.institute != null)
            message.institute = object.institute | 0;
        if (object.branch != null)
            message.branch = object.branch | 0;
        if (object.schema != null)
            message.schema = object.schema | 0;
        return message;
    };

    /**
     * Creates a plain object from a Header message. Also converts values to other types if specified.
     * @function toObject
     * @memberof Header
     * @static
     * @param {Header} message Header
     * @param {$protobuf.IConversionOptions} [options] Conversion options
     * @returns {Object.<string,*>} Plain object
     */
    Header.toObject = function toObject(message, options) {
        if (!options)
            options = {};
        var object = {};
        if (options.defaults) {
            object.university = 0;
            object.institute = 0;
            object.branch = 0;
            object.schema = 0;
        }
        if (message.university != null && message.hasOwnProperty("university"))
            object.university = message.university;
        if (message.institute != null && message.hasOwnProperty("institute"))
            object.institute = message.institute;
        if (message.branch != null && message.hasOwnProperty("branch"))
            object.branch = message.branch;
        if (message.schema != null && message.hasOwnProperty("schema"))
            object.schema = message.schema;
        return object;
    };

    /**
     * Converts this Header to JSON.
     * @function toJSON
     * @memberof Header
     * @instance
     * @returns {Object.<string,*>} JSON object
     */
    Header.prototype.toJSON = function toJSON() {
        return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
    };

    /**
     * Gets the default type url for Header
     * @function getTypeUrl
     * @memberof Header
     * @static
     * @param {string} [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns {string} The default type url
     */
    Header.getTypeUrl = function getTypeUrl(typeUrlPrefix) {
        if (typeUrlPrefix === undefined) {
            typeUrlPrefix = "type.googleapis.com";
        }
        return typeUrlPrefix + "/Header";
    };

    return Header;
})();

$root.Meta = (function() {

    /**
     * Properties of a Meta.
     * @exports IMeta
     * @interface IMeta
     * @property {string|null} [id] Meta id
     * @property {number|null} [total] Meta total
     * @property {Object.<string,string>|null} [other] Meta other
     */

    /**
     * Constructs a new Meta.
     * @exports Meta
     * @classdesc Represents a Meta.
     * @implements IMeta
     * @constructor
     * @param {IMeta=} [properties] Properties to set
     */
    function Meta(properties) {
        this.other = {};
        if (properties)
            for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                if (properties[keys[i]] != null)
                    this[keys[i]] = properties[keys[i]];
    }

    /**
     * Meta id.
     * @member {string} id
     * @memberof Meta
     * @instance
     */
    Meta.prototype.id = "";

    /**
     * Meta total.
     * @member {number} total
     * @memberof Meta
     * @instance
     */
    Meta.prototype.total = 0;

    /**
     * Meta other.
     * @member {Object.<string,string>} other
     * @memberof Meta
     * @instance
     */
    Meta.prototype.other = $util.emptyObject;

    /**
     * Creates a new Meta instance using the specified properties.
     * @function create
     * @memberof Meta
     * @static
     * @param {IMeta=} [properties] Properties to set
     * @returns {Meta} Meta instance
     */
    Meta.create = function create(properties) {
        return new Meta(properties);
    };

    /**
     * Encodes the specified Meta message. Does not implicitly {@link Meta.verify|verify} messages.
     * @function encode
     * @memberof Meta
     * @static
     * @param {IMeta} message Meta message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Meta.encode = function encode(message, writer) {
        if (!writer)
            writer = $Writer.create();
        if (message.id != null && Object.hasOwnProperty.call(message, "id"))
            writer.uint32(/* id 1, wireType 2 =*/10).string(message.id);
        if (message.total != null && Object.hasOwnProperty.call(message, "total"))
            writer.uint32(/* id 2, wireType 0 =*/16).int32(message.total);
        if (message.other != null && Object.hasOwnProperty.call(message, "other"))
            for (var keys = Object.keys(message.other), i = 0; i < keys.length; ++i)
                writer.uint32(/* id 3, wireType 2 =*/26).fork().uint32(/* id 1, wireType 2 =*/10).string(keys[i]).uint32(/* id 2, wireType 2 =*/18).string(message.other[keys[i]]).ldelim();
        return writer;
    };

    /**
     * Encodes the specified Meta message, length delimited. Does not implicitly {@link Meta.verify|verify} messages.
     * @function encodeDelimited
     * @memberof Meta
     * @static
     * @param {IMeta} message Meta message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Meta.encodeDelimited = function encodeDelimited(message, writer) {
        return this.encode(message, writer).ldelim();
    };

    /**
     * Decodes a Meta message from the specified reader or buffer.
     * @function decode
     * @memberof Meta
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @param {number} [length] Message length if known beforehand
     * @returns {Meta} Meta
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Meta.decode = function decode(reader, length, error) {
        if (!(reader instanceof $Reader))
            reader = $Reader.create(reader);
        var end = length === undefined ? reader.len : reader.pos + length, message = new $root.Meta(), key, value;
        while (reader.pos < end) {
            var tag = reader.uint32();
            if (tag === error)
                break;
            switch (tag >>> 3) {
            case 1: {
                    message.id = reader.string();
                    break;
                }
            case 2: {
                    message.total = reader.int32();
                    break;
                }
            case 3: {
                    if (message.other === $util.emptyObject)
                        message.other = {};
                    var end2 = reader.uint32() + reader.pos;
                    key = "";
                    value = "";
                    while (reader.pos < end2) {
                        var tag2 = reader.uint32();
                        switch (tag2 >>> 3) {
                        case 1:
                            key = reader.string();
                            break;
                        case 2:
                            value = reader.string();
                            break;
                        default:
                            reader.skipType(tag2 & 7);
                            break;
                        }
                    }
                    message.other[key] = value;
                    break;
                }
            default:
                reader.skipType(tag & 7);
                break;
            }
        }
        return message;
    };

    /**
     * Decodes a Meta message from the specified reader or buffer, length delimited.
     * @function decodeDelimited
     * @memberof Meta
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @returns {Meta} Meta
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Meta.decodeDelimited = function decodeDelimited(reader) {
        if (!(reader instanceof $Reader))
            reader = new $Reader(reader);
        return this.decode(reader, reader.uint32());
    };

    /**
     * Verifies a Meta message.
     * @function verify
     * @memberof Meta
     * @static
     * @param {Object.<string,*>} message Plain object to verify
     * @returns {string|null} `null` if valid, otherwise the reason why it is not
     */
    Meta.verify = function verify(message) {
        if (typeof message !== "object" || message === null)
            return "object expected";
        if (message.id != null && message.hasOwnProperty("id"))
            if (!$util.isString(message.id))
                return "id: string expected";
        if (message.total != null && message.hasOwnProperty("total"))
            if (!$util.isInteger(message.total))
                return "total: integer expected";
        if (message.other != null && message.hasOwnProperty("other")) {
            if (!$util.isObject(message.other))
                return "other: object expected";
            var key = Object.keys(message.other);
            for (var i = 0; i < key.length; ++i)
                if (!$util.isString(message.other[key[i]]))
                    return "other: string{k:string} expected";
        }
        return null;
    };

    /**
     * Creates a Meta message from a plain object. Also converts values to their respective internal types.
     * @function fromObject
     * @memberof Meta
     * @static
     * @param {Object.<string,*>} object Plain object
     * @returns {Meta} Meta
     */
    Meta.fromObject = function fromObject(object) {
        if (object instanceof $root.Meta)
            return object;
        var message = new $root.Meta();
        if (object.id != null)
            message.id = String(object.id);
        if (object.total != null)
            message.total = object.total | 0;
        if (object.other) {
            if (typeof object.other !== "object")
                throw TypeError(".Meta.other: object expected");
            message.other = {};
            for (var keys = Object.keys(object.other), i = 0; i < keys.length; ++i)
                message.other[keys[i]] = String(object.other[keys[i]]);
        }
        return message;
    };

    /**
     * Creates a plain object from a Meta message. Also converts values to other types if specified.
     * @function toObject
     * @memberof Meta
     * @static
     * @param {Meta} message Meta
     * @param {$protobuf.IConversionOptions} [options] Conversion options
     * @returns {Object.<string,*>} Plain object
     */
    Meta.toObject = function toObject(message, options) {
        if (!options)
            options = {};
        var object = {};
        if (options.objects || options.defaults)
            object.other = {};
        if (options.defaults) {
            object.id = "";
            object.total = 0;
        }
        if (message.id != null && message.hasOwnProperty("id"))
            object.id = message.id;
        if (message.total != null && message.hasOwnProperty("total"))
            object.total = message.total;
        var keys2;
        if (message.other && (keys2 = Object.keys(message.other)).length) {
            object.other = {};
            for (var j = 0; j < keys2.length; ++j)
                object.other[keys2[j]] = message.other[keys2[j]];
        }
        return object;
    };

    /**
     * Converts this Meta to JSON.
     * @function toJSON
     * @memberof Meta
     * @instance
     * @returns {Object.<string,*>} JSON object
     */
    Meta.prototype.toJSON = function toJSON() {
        return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
    };

    /**
     * Gets the default type url for Meta
     * @function getTypeUrl
     * @memberof Meta
     * @static
     * @param {string} [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns {string} The default type url
     */
    Meta.getTypeUrl = function getTypeUrl(typeUrlPrefix) {
        if (typeUrlPrefix === undefined) {
            typeUrlPrefix = "type.googleapis.com";
        }
        return typeUrlPrefix + "/Meta";
    };

    return Meta;
})();

$root.Subject = (function() {

    /**
     * Properties of a Subject.
     * @exports ISubject
     * @interface ISubject
     * @property {Object.<string,IMeta>|null} [subject] Subject subject
     */

    /**
     * Constructs a new Subject.
     * @exports Subject
     * @classdesc Represents a Subject.
     * @implements ISubject
     * @constructor
     * @param {ISubject=} [properties] Properties to set
     */
    function Subject(properties) {
        this.subject = {};
        if (properties)
            for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                if (properties[keys[i]] != null)
                    this[keys[i]] = properties[keys[i]];
    }

    /**
     * Subject subject.
     * @member {Object.<string,IMeta>} subject
     * @memberof Subject
     * @instance
     */
    Subject.prototype.subject = $util.emptyObject;

    /**
     * Creates a new Subject instance using the specified properties.
     * @function create
     * @memberof Subject
     * @static
     * @param {ISubject=} [properties] Properties to set
     * @returns {Subject} Subject instance
     */
    Subject.create = function create(properties) {
        return new Subject(properties);
    };

    /**
     * Encodes the specified Subject message. Does not implicitly {@link Subject.verify|verify} messages.
     * @function encode
     * @memberof Subject
     * @static
     * @param {ISubject} message Subject message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Subject.encode = function encode(message, writer) {
        if (!writer)
            writer = $Writer.create();
        if (message.subject != null && Object.hasOwnProperty.call(message, "subject"))
            for (var keys = Object.keys(message.subject), i = 0; i < keys.length; ++i) {
                writer.uint32(/* id 1, wireType 2 =*/10).fork().uint32(/* id 1, wireType 2 =*/10).string(keys[i]);
                $root.Meta.encode(message.subject[keys[i]], writer.uint32(/* id 2, wireType 2 =*/18).fork()).ldelim().ldelim();
            }
        return writer;
    };

    /**
     * Encodes the specified Subject message, length delimited. Does not implicitly {@link Subject.verify|verify} messages.
     * @function encodeDelimited
     * @memberof Subject
     * @static
     * @param {ISubject} message Subject message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    Subject.encodeDelimited = function encodeDelimited(message, writer) {
        return this.encode(message, writer).ldelim();
    };

    /**
     * Decodes a Subject message from the specified reader or buffer.
     * @function decode
     * @memberof Subject
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @param {number} [length] Message length if known beforehand
     * @returns {Subject} Subject
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Subject.decode = function decode(reader, length, error) {
        if (!(reader instanceof $Reader))
            reader = $Reader.create(reader);
        var end = length === undefined ? reader.len : reader.pos + length, message = new $root.Subject(), key, value;
        while (reader.pos < end) {
            var tag = reader.uint32();
            if (tag === error)
                break;
            switch (tag >>> 3) {
            case 1: {
                    if (message.subject === $util.emptyObject)
                        message.subject = {};
                    var end2 = reader.uint32() + reader.pos;
                    key = "";
                    value = null;
                    while (reader.pos < end2) {
                        var tag2 = reader.uint32();
                        switch (tag2 >>> 3) {
                        case 1:
                            key = reader.string();
                            break;
                        case 2:
                            value = $root.Meta.decode(reader, reader.uint32());
                            break;
                        default:
                            reader.skipType(tag2 & 7);
                            break;
                        }
                    }
                    message.subject[key] = value;
                    break;
                }
            default:
                reader.skipType(tag & 7);
                break;
            }
        }
        return message;
    };

    /**
     * Decodes a Subject message from the specified reader or buffer, length delimited.
     * @function decodeDelimited
     * @memberof Subject
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @returns {Subject} Subject
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    Subject.decodeDelimited = function decodeDelimited(reader) {
        if (!(reader instanceof $Reader))
            reader = new $Reader(reader);
        return this.decode(reader, reader.uint32());
    };

    /**
     * Verifies a Subject message.
     * @function verify
     * @memberof Subject
     * @static
     * @param {Object.<string,*>} message Plain object to verify
     * @returns {string|null} `null` if valid, otherwise the reason why it is not
     */
    Subject.verify = function verify(message) {
        if (typeof message !== "object" || message === null)
            return "object expected";
        if (message.subject != null && message.hasOwnProperty("subject")) {
            if (!$util.isObject(message.subject))
                return "subject: object expected";
            var key = Object.keys(message.subject);
            for (var i = 0; i < key.length; ++i) {
                var error = $root.Meta.verify(message.subject[key[i]]);
                if (error)
                    return "subject." + error;
            }
        }
        return null;
    };

    /**
     * Creates a Subject message from a plain object. Also converts values to their respective internal types.
     * @function fromObject
     * @memberof Subject
     * @static
     * @param {Object.<string,*>} object Plain object
     * @returns {Subject} Subject
     */
    Subject.fromObject = function fromObject(object) {
        if (object instanceof $root.Subject)
            return object;
        var message = new $root.Subject();
        if (object.subject) {
            if (typeof object.subject !== "object")
                throw TypeError(".Subject.subject: object expected");
            message.subject = {};
            for (var keys = Object.keys(object.subject), i = 0; i < keys.length; ++i) {
                if (typeof object.subject[keys[i]] !== "object")
                    throw TypeError(".Subject.subject: object expected");
                message.subject[keys[i]] = $root.Meta.fromObject(object.subject[keys[i]]);
            }
        }
        return message;
    };

    /**
     * Creates a plain object from a Subject message. Also converts values to other types if specified.
     * @function toObject
     * @memberof Subject
     * @static
     * @param {Subject} message Subject
     * @param {$protobuf.IConversionOptions} [options] Conversion options
     * @returns {Object.<string,*>} Plain object
     */
    Subject.toObject = function toObject(message, options) {
        if (!options)
            options = {};
        var object = {};
        if (options.objects || options.defaults)
            object.subject = {};
        var keys2;
        if (message.subject && (keys2 = Object.keys(message.subject)).length) {
            object.subject = {};
            for (var j = 0; j < keys2.length; ++j)
                object.subject[keys2[j]] = $root.Meta.toObject(message.subject[keys2[j]], options);
        }
        return object;
    };

    /**
     * Converts this Subject to JSON.
     * @function toJSON
     * @memberof Subject
     * @instance
     * @returns {Object.<string,*>} JSON object
     */
    Subject.prototype.toJSON = function toJSON() {
        return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
    };

    /**
     * Gets the default type url for Subject
     * @function getTypeUrl
     * @memberof Subject
     * @static
     * @param {string} [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns {string} The default type url
     */
    Subject.getTypeUrl = function getTypeUrl(typeUrlPrefix) {
        if (typeUrlPrefix === undefined) {
            typeUrlPrefix = "type.googleapis.com";
        }
        return typeUrlPrefix + "/Subject";
    };

    return Subject;
})();

$root.CardData = (function() {

    /**
     * Properties of a CardData.
     * @exports ICardData
     * @interface ICardData
     * @property {IHeader|null} [header] CardData header
     * @property {Object.<string,ISubject>|null} [semester] CardData semester
     * @property {Object.<string,string>|null} [personal] CardData personal
     * @property {Object.<string,Uint8Array>|null} [image] CardData image
     */

    /**
     * Constructs a new CardData.
     * @exports CardData
     * @classdesc Represents a CardData.
     * @implements ICardData
     * @constructor
     * @param {ICardData=} [properties] Properties to set
     */
    function CardData(properties) {
        this.semester = {};
        this.personal = {};
        this.image = {};
        if (properties)
            for (var keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                if (properties[keys[i]] != null)
                    this[keys[i]] = properties[keys[i]];
    }

    /**
     * CardData header.
     * @member {IHeader|null|undefined} header
     * @memberof CardData
     * @instance
     */
    CardData.prototype.header = null;

    /**
     * CardData semester.
     * @member {Object.<string,ISubject>} semester
     * @memberof CardData
     * @instance
     */
    CardData.prototype.semester = $util.emptyObject;

    /**
     * CardData personal.
     * @member {Object.<string,string>} personal
     * @memberof CardData
     * @instance
     */
    CardData.prototype.personal = $util.emptyObject;

    /**
     * CardData image.
     * @member {Object.<string,Uint8Array>} image
     * @memberof CardData
     * @instance
     */
    CardData.prototype.image = $util.emptyObject;

    /**
     * Creates a new CardData instance using the specified properties.
     * @function create
     * @memberof CardData
     * @static
     * @param {ICardData=} [properties] Properties to set
     * @returns {CardData} CardData instance
     */
    CardData.create = function create(properties) {
        return new CardData(properties);
    };

    /**
     * Encodes the specified CardData message. Does not implicitly {@link CardData.verify|verify} messages.
     * @function encode
     * @memberof CardData
     * @static
     * @param {ICardData} message CardData message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    CardData.encode = function encode(message, writer) {
        if (!writer)
            writer = $Writer.create();
        if (message.header != null && Object.hasOwnProperty.call(message, "header"))
            $root.Header.encode(message.header, writer.uint32(/* id 1, wireType 2 =*/10).fork()).ldelim();
        if (message.semester != null && Object.hasOwnProperty.call(message, "semester"))
            for (var keys = Object.keys(message.semester), i = 0; i < keys.length; ++i) {
                writer.uint32(/* id 2, wireType 2 =*/18).fork().uint32(/* id 1, wireType 0 =*/8).int32(keys[i]);
                $root.Subject.encode(message.semester[keys[i]], writer.uint32(/* id 2, wireType 2 =*/18).fork()).ldelim().ldelim();
            }
        if (message.personal != null && Object.hasOwnProperty.call(message, "personal"))
            for (var keys = Object.keys(message.personal), i = 0; i < keys.length; ++i)
                writer.uint32(/* id 3, wireType 2 =*/26).fork().uint32(/* id 1, wireType 2 =*/10).string(keys[i]).uint32(/* id 2, wireType 2 =*/18).string(message.personal[keys[i]]).ldelim();
        if (message.image != null && Object.hasOwnProperty.call(message, "image"))
            for (var keys = Object.keys(message.image), i = 0; i < keys.length; ++i)
                writer.uint32(/* id 4, wireType 2 =*/34).fork().uint32(/* id 1, wireType 2 =*/10).string(keys[i]).uint32(/* id 2, wireType 2 =*/18).bytes(message.image[keys[i]]).ldelim();
        return writer;
    };

    /**
     * Encodes the specified CardData message, length delimited. Does not implicitly {@link CardData.verify|verify} messages.
     * @function encodeDelimited
     * @memberof CardData
     * @static
     * @param {ICardData} message CardData message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    CardData.encodeDelimited = function encodeDelimited(message, writer) {
        return this.encode(message, writer).ldelim();
    };

    /**
     * Decodes a CardData message from the specified reader or buffer.
     * @function decode
     * @memberof CardData
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @param {number} [length] Message length if known beforehand
     * @returns {CardData} CardData
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    CardData.decode = function decode(reader, length, error) {
        if (!(reader instanceof $Reader))
            reader = $Reader.create(reader);
        var end = length === undefined ? reader.len : reader.pos + length, message = new $root.CardData(), key, value;
        while (reader.pos < end) {
            var tag = reader.uint32();
            if (tag === error)
                break;
            switch (tag >>> 3) {
            case 1: {
                    message.header = $root.Header.decode(reader, reader.uint32());
                    break;
                }
            case 2: {
                    if (message.semester === $util.emptyObject)
                        message.semester = {};
                    var end2 = reader.uint32() + reader.pos;
                    key = 0;
                    value = null;
                    while (reader.pos < end2) {
                        var tag2 = reader.uint32();
                        switch (tag2 >>> 3) {
                        case 1:
                            key = reader.int32();
                            break;
                        case 2:
                            value = $root.Subject.decode(reader, reader.uint32());
                            break;
                        default:
                            reader.skipType(tag2 & 7);
                            break;
                        }
                    }
                    message.semester[key] = value;
                    break;
                }
            case 3: {
                    if (message.personal === $util.emptyObject)
                        message.personal = {};
                    var end2 = reader.uint32() + reader.pos;
                    key = "";
                    value = "";
                    while (reader.pos < end2) {
                        var tag2 = reader.uint32();
                        switch (tag2 >>> 3) {
                        case 1:
                            key = reader.string();
                            break;
                        case 2:
                            value = reader.string();
                            break;
                        default:
                            reader.skipType(tag2 & 7);
                            break;
                        }
                    }
                    message.personal[key] = value;
                    break;
                }
            case 4: {
                    if (message.image === $util.emptyObject)
                        message.image = {};
                    var end2 = reader.uint32() + reader.pos;
                    key = "";
                    value = [];
                    while (reader.pos < end2) {
                        var tag2 = reader.uint32();
                        switch (tag2 >>> 3) {
                        case 1:
                            key = reader.string();
                            break;
                        case 2:
                            value = reader.bytes();
                            break;
                        default:
                            reader.skipType(tag2 & 7);
                            break;
                        }
                    }
                    message.image[key] = value;
                    break;
                }
            default:
                reader.skipType(tag & 7);
                break;
            }
        }
        return message;
    };

    /**
     * Decodes a CardData message from the specified reader or buffer, length delimited.
     * @function decodeDelimited
     * @memberof CardData
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @returns {CardData} CardData
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    CardData.decodeDelimited = function decodeDelimited(reader) {
        if (!(reader instanceof $Reader))
            reader = new $Reader(reader);
        return this.decode(reader, reader.uint32());
    };

    /**
     * Verifies a CardData message.
     * @function verify
     * @memberof CardData
     * @static
     * @param {Object.<string,*>} message Plain object to verify
     * @returns {string|null} `null` if valid, otherwise the reason why it is not
     */
    CardData.verify = function verify(message) {
        if (typeof message !== "object" || message === null)
            return "object expected";
        if (message.header != null && message.hasOwnProperty("header")) {
            var error = $root.Header.verify(message.header);
            if (error)
                return "header." + error;
        }
        if (message.semester != null && message.hasOwnProperty("semester")) {
            if (!$util.isObject(message.semester))
                return "semester: object expected";
            var key = Object.keys(message.semester);
            for (var i = 0; i < key.length; ++i) {
                if (!$util.key32Re.test(key[i]))
                    return "semester: integer key{k:int32} expected";
                {
                    var error = $root.Subject.verify(message.semester[key[i]]);
                    if (error)
                        return "semester." + error;
                }
            }
        }
        if (message.personal != null && message.hasOwnProperty("personal")) {
            if (!$util.isObject(message.personal))
                return "personal: object expected";
            var key = Object.keys(message.personal);
            for (var i = 0; i < key.length; ++i)
                if (!$util.isString(message.personal[key[i]]))
                    return "personal: string{k:string} expected";
        }
        if (message.image != null && message.hasOwnProperty("image")) {
            if (!$util.isObject(message.image))
                return "image: object expected";
            var key = Object.keys(message.image);
            for (var i = 0; i < key.length; ++i)
                if (!(message.image[key[i]] && typeof message.image[key[i]].length === "number" || $util.isString(message.image[key[i]])))
                    return "image: buffer{k:string} expected";
        }
        return null;
    };

    /**
     * Creates a CardData message from a plain object. Also converts values to their respective internal types.
     * @function fromObject
     * @memberof CardData
     * @static
     * @param {Object.<string,*>} object Plain object
     * @returns {CardData} CardData
     */
    CardData.fromObject = function fromObject(object) {
        if (object instanceof $root.CardData)
            return object;
        var message = new $root.CardData();
        if (object.header != null) {
            if (typeof object.header !== "object")
                throw TypeError(".CardData.header: object expected");
            message.header = $root.Header.fromObject(object.header);
        }
        if (object.semester) {
            if (typeof object.semester !== "object")
                throw TypeError(".CardData.semester: object expected");
            message.semester = {};
            for (var keys = Object.keys(object.semester), i = 0; i < keys.length; ++i) {
                if (typeof object.semester[keys[i]] !== "object")
                    throw TypeError(".CardData.semester: object expected");
                message.semester[keys[i]] = $root.Subject.fromObject(object.semester[keys[i]]);
            }
        }
        if (object.personal) {
            if (typeof object.personal !== "object")
                throw TypeError(".CardData.personal: object expected");
            message.personal = {};
            for (var keys = Object.keys(object.personal), i = 0; i < keys.length; ++i)
                message.personal[keys[i]] = String(object.personal[keys[i]]);
        }
        if (object.image) {
            if (typeof object.image !== "object")
                throw TypeError(".CardData.image: object expected");
            message.image = {};
            for (var keys = Object.keys(object.image), i = 0; i < keys.length; ++i)
                if (typeof object.image[keys[i]] === "string")
                    $util.base64.decode(object.image[keys[i]], message.image[keys[i]] = $util.newBuffer($util.base64.length(object.image[keys[i]])), 0);
                else if (object.image[keys[i]].length >= 0)
                    message.image[keys[i]] = object.image[keys[i]];
        }
        return message;
    };

    /**
     * Creates a plain object from a CardData message. Also converts values to other types if specified.
     * @function toObject
     * @memberof CardData
     * @static
     * @param {CardData} message CardData
     * @param {$protobuf.IConversionOptions} [options] Conversion options
     * @returns {Object.<string,*>} Plain object
     */
    CardData.toObject = function toObject(message, options) {
        if (!options)
            options = {};
        var object = {};
        if (options.objects || options.defaults) {
            object.semester = {};
            object.personal = {};
            object.image = {};
        }
        if (options.defaults)
            object.header = null;
        if (message.header != null && message.hasOwnProperty("header"))
            object.header = $root.Header.toObject(message.header, options);
        var keys2;
        if (message.semester && (keys2 = Object.keys(message.semester)).length) {
            object.semester = {};
            for (var j = 0; j < keys2.length; ++j)
                object.semester[keys2[j]] = $root.Subject.toObject(message.semester[keys2[j]], options);
        }
        if (message.personal && (keys2 = Object.keys(message.personal)).length) {
            object.personal = {};
            for (var j = 0; j < keys2.length; ++j)
                object.personal[keys2[j]] = message.personal[keys2[j]];
        }
        if (message.image && (keys2 = Object.keys(message.image)).length) {
            object.image = {};
            for (var j = 0; j < keys2.length; ++j)
                object.image[keys2[j]] = options.bytes === String ? $util.base64.encode(message.image[keys2[j]], 0, message.image[keys2[j]].length) : options.bytes === Array ? Array.prototype.slice.call(message.image[keys2[j]]) : message.image[keys2[j]];
        }
        return object;
    };

    /**
     * Converts this CardData to JSON.
     * @function toJSON
     * @memberof CardData
     * @instance
     * @returns {Object.<string,*>} JSON object
     */
    CardData.prototype.toJSON = function toJSON() {
        return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
    };

    /**
     * Gets the default type url for CardData
     * @function getTypeUrl
     * @memberof CardData
     * @static
     * @param {string} [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns {string} The default type url
     */
    CardData.getTypeUrl = function getTypeUrl(typeUrlPrefix) {
        if (typeUrlPrefix === undefined) {
            typeUrlPrefix = "type.googleapis.com";
        }
        return typeUrlPrefix + "/CardData";
    };

    return CardData;
})();

module.exports = $root;
