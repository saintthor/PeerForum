function UBBObj( BtnArea, TextArea )
{
    var ubb = this;
    this.BtnArea = BtnArea;
    this.TextArea = TextArea;
    
    //**************************************************************************
    var LabelTree = function( Labels, ObjStr )          //标签树
    {
        var Tree = this;
        this.MaxLayer = 30;              //最大层数
        this.Nodes = [];
        this.Branches = [];
        this.Html = ObjStr;
        //alert( Html );
        
        this.Init = function()
        {
            _( Labels ).chain().keys().each( function( k )
            {
                if( Labels[k].br )
                {
                    return;
                }
                var re = Labels[k].re || new RegExp( '\\[\\/?' + k + '(=[^\[]*?)?\\]', 'i' );
                var start = 0;
                for( ;; )
                {
                    var pos = Tree.Html.slice( start ).search( re );
                    var LbStrs = Tree.Html.slice( start ).match( re );
                    if( pos < 0 )
                    {
                        break;
                    }
                    start += pos + 1;
                    Tree.Nodes.push( [[start - 1, start + LbStrs[0].length - 1], k, Number( Tree.Html[start] === '/' ), LbStrs[0]] );
                    //alert( start + '|' + LbStr + '|' + LbStr.length );
                }
            } );
            
            this.Nodes.sort( function( m, n )
            {
                return m[0][0] - n[0][0];
            } );
            
            //alert( this.Nodes.join( '\n' ));
            
            var TextNodes = [];
            var start = 0, end = this.Html.length - 1, n00 = 0;
            _( this.Nodes ).each( function( n )
            {
                n00 = n[0][0];
                //alert( start + ',' + n[0] );
                if( n00 > start )
                {
                    //alert( 'text' + ',' + [start, n00] );
                    TextNodes.push( [[start, n00], 'text', false, Tree.Html.slice( start, n00 )] );
                }
                start = n[0][1];
            } );
            
            if( start <= end )
            {
                TextNodes.push( [[start, end], 'text', false, Tree.Html.slice( start )] );
            }
            
            this.Nodes = this.Nodes.concat( TextNodes );
            
            this.Nodes.sort( function( m, n )
            {
                return m[0][0] - n[0][0];
            } );
            
            //alert( this.Nodes.join( '\n' ));
            if( this.Nodes.length > 0 )
            {
                this.ChkStruct();
            }
        };
        
        this.Show = function( ParentLabel )      //转义标签，显示内容
        {
            var Labels = ParentLabel ? ParentLabel.Childs : this.Branches;
            var LabelHtml = '';
            
            _( Labels ).each( function( Label )
            {
                if( Label.Name != 'text' || !ParentLabel || !ParentLabel.Type.NoText )
                {
                    var ChildsHtml = Tree.Show( Label );
                    try
                    {
                        LabelHtml += Label.Type.Express( ChildsHtml, Label.Text );
                    }
                    catch( e )
                    {
                        LabelHtml += Label.Text + ChildsHtml + '[/' + Label.Name + ']';
                    }
                }
            } );
            //alert( LabelHtml );
            return LabelHtml;
        };
        
        this.ChkStruct = function()
        {
            var LeafStack = [];
            var Leaf = this.Branches = [];
            var LastLabel = null;
            var Index = 0;
            //var HalfLabel = false;
            _( Tree.Nodes ).each( function( n )
            {
                //alert( n );
                if( n[2] )                  //尾标签
                {
                    if( !LastLabel )
                    {
                        throw "LabelStartError," + n[1] + ',' + n[0];
                    }
                    //alert( LastLabel.Name );
                    if( LastLabel.Closed )
                    {
                        if( LastLabel.Name === 'r' && n[1] === 'r' && LastLabel.Childs.length === 0 )
                        {
                            LastLabel.Childs.push( new LabelObj( 'text', -1, n[3] ));
                            LastLabel.Close( Index++ );
                            return;
                        }
                        
                        Leaf = LeafStack.pop();
                        if( !Leaf )
                        {
                            throw "LabelNoHeadErr," + n[1] + "," + n[0];
                        }
                        LastLabel = Leaf[Leaf.length - 1];
                    }
                    if( LastLabel.Name == n[1] )
                    {
                        LastLabel.Close( Index++ );
                    }
                    else if( LastLabel.Name === 'r' )
                    {
                        if( LastLabel.Childs.length > 0 )
                        {
                            throw "LabelMoreInRErr," + n[1] + "," + n[0];
                        }
                        LastLabel.Childs.push( new LabelObj( 'text', -1, n[3] ));
                        Index++;
                    }
                    else
                    {
                        throw "LabelPairErr," + n[1] + "," + n[0];
                    }
                }
                else                        //首标签
                {
                    var Label;
                    
                    if( n[1] === 'text' )
                    {
                        Label = new LabelObj( 'text', -1, n[3] );
                    }
                    else
                    {
                        Label = new LabelObj( n[1], Index++, n[3] );    //n[3]是首标签的串
                    }
                    
                    if( LastLabel && !LastLabel.Closed )        //下层标签
                    {
                        //alert( Label.MustIn );
                        if( LastLabel.Name === 'r' )
                        {
                            if( LastLabel.Childs.length > 0 )
                            {
                                throw "LabelMoreInRErr," + n[1] + "," + n[0];
                            }
                            LastLabel.Childs.push( new LabelObj( 'text', -1, n[3] ));
                            return;
                        }
                        
                        if( LeafStack.length >= Tree.MaxLayer )
                        {
                            throw "LabelMaxLayerErr," + n[1] + "," + n[0];
                        }
                        LeafStack.push( Leaf );
                        Leaf = LastLabel.Childs;
                    }
                    
                    if( !Label.Type.InSelf )            //不能在同名标签之内
                    {
                        _( LeafStack ).each( function( lf )
                        {
                            var OutLabel = lf[lf.length - 1];
                            if( OutLabel.Name === Label.Name )
                            {
                                throw "LabelInSelfErr," + n[1] + "," + n[0];
                            }
                        } );
                    }
                    
                    if( Label.Type.MustIn )             //必须在某种标签之内
                    {
                        var Match = false;
                        
                        if( LeafStack.length > 0 )
                        {
                            var lf = LeafStack[LeafStack.length - 1];
                            Match = lf[lf.length - 1].Name == Label.Type.MustIn
                        }

                        if( !Match )
                        {
                            throw "LabelMustInErr," + n[1] + "," + n[0];
                        }
                    }
                    
                    if( Label.Type.NotIn && LeafStack.length > 0 )              //不能在某种标签之内
                    {
                        var lf = LeafStack[LeafStack.length - 1];
                        var ParentName = lf[lf.length - 1].Name;
                        if( _( Label.Type.NotIn ).contains( ParentName ))
                        {
                            throw "LabelNotInErr," + n[1] + "," + n[0];
                        }
                    }
                    
                    Leaf.push( Label );
                    if( Label.Type.Num == 1 )         //单标签
                    {
                        Label.Close( Index - 1 );
                    }
                    
                    LastLabel = Label;
                }
            } );
            
            if( Leaf != this.Branches || !LastLabel.Closed )
            {
                throw "LabelNoTailErr";
            }
        };
        
        this.Init();
    };
    
    //**************************************************************************
    var LabelType = {
        
        b: { Num: 2, note: '粗体', },
        i: { Num: 2, note: '斜体', },
        
        u: {
            Num: 2, note: '带下划线',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[u(=(.*?))?\]/i );
                if( m[1] && m[2] )
                {
                    var Title = m[2].slice( 0, 200 );
                    return '<u title="' + Title + '" style="cursor:pointer">' + Content + '</u>';
                }
                return '<u>' + Content + '</u>';
            },
        },
                
        s: {
            Num: 2, note: '带删除线',
            Express: function( Content, LabelHead )
            {
                return '<s><strike>' + Content + '</strike></s>';
            },
        },
        
        sup: { Num: 2, InSelf: true, note: '上标', },
        sub: { Num: 2, note: '下标', },
        
        div: {
            Num: 2, FirstLabel: '[div=#ffffcc]', InSelf: true, note: '块',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[div(=(.*?))?\]/i );
                var Param = m[1] ? this.ParseParam( m[2], 'background-color' ) : {};
                //alert( JSON.stringify( Param ));
                var StyleStr = this.GetStyleStr( Param );
                //alert( StyleStr );
                return '<div class="common" style="' + StyleStr + '">' + Content + '</div>';
            },
        },
        
        color: {
            Num: 2, FirstLabel: '[color=blue]', InSelf: true, note: '文字颜色', 
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[color=(.*?)\]/i );
                return '<span style="color:' + m[1] + '">' + Content + '</span>';
            },
        },
        
        size: {
            Num: 2, FirstLabel: '[size=5]', InSelf: true, note: '文字尺寸',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[size=([\d\.]*?)\]/i );
                return '<span style="font-size:' + m[1] + 'em">' + Content + '</span>';
                //return '<font size=' + m[1] + '>' + Content + '</font>';
            },
        },
        
        r: {
            Num: 2, note: '禁止转义',
            Insert: function()        //
            {
                var SelStart = ubb.TextArea[0].selectionStart;
                var SelEnd = ubb.TextArea[0].selectionEnd;
                var Content = ubb.TextArea.val();
                
                if( SelStart == SelEnd )
                {
                    Content = Content.slice( 0, SelStart ) + '[r][/r]' + Content.slice( SelStart, Content.length );
                }
                else
                {
                    var Quoted = Content.slice( SelStart, SelEnd );
                    //alert( Quoted );
                    var m = Quoted.match( /^\[(.*?)(=^\]*?)?\]$/i );
                    
                    if( !m || !m[1] )
                    {
                        m = Quoted.match( /^\[\/(.*?)\]$/i );
                    }
                    if( !m || !m[1] )
                    {
                        alert( '错误：只能选中一个标签。' );
                        return;
                    }

                    if( !_( LabelType ).chain().keys().contains( m[1] ))
                    {
                        alert( '错误：选中的标签无效。' );
                        return;
                    }
                    
                    Content = Content.slice( 0, SelEnd ) + '[/r]' + Content.slice( SelEnd, Content.length );
                    Content = Content.slice( 0, SelStart ) + '[r]' + Content.slice( SelStart, Content.length );
                }

                ubb.TextArea.val( Content );
            },
            
            Express: function( Content, LabelHead )
            {
                return Content;
            },
        },
        
        hr: {
            Num: 1, note: '水平分隔线',
            Express: function( Content, LabelHead )
            {
                return '<hr>';
            },
        },
        
        url: {
            Num: 2, FirstLabel: '[url=www.djdq.org]', Content: '大江东去科幻论坛', NotIn: ['title', 'goto', 'pl'], note: '链接',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /^\[url=(.*?)\]/i );
                var Address = m[1];
                if( !Address.match( /^http:\/\//i ) && !Address.match( /^https:\/\//i ))
                {
                    Address = 'http://' + Address;
                }
                //return Address;
                return '<a href="' + Address + '" target="_blank">' + Content + '</a>';
            },
        },
        
        atcl: {
            Num: 2, FirstLabel: '[pl=78037]', Content: '《论坛总帮助》', NotIn: ['title', 'goto', 'url'], note: '帖子链接',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /^\[pl=(\d*?)\]/i );
                return '<a class="green" href="post?v=2&p=' + m[1] + '">' + Content + '</a>';
            },
        },
        
        image: {
            Num: 1, FirstLabel: '[image=pic/djdq.jpg]', note: '图片',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[image=(.*?)\]/i );
                return '<img src="' + m[1] + '"/>';
            },
        },
        
        text: {
            Num: 1, Static: true,
            Express: function( Content, Text )
            {
                return Text;
            },
        },
        
        title: {
            Num: 2, Static: true, NotIn: ['color', 'url', 'b', 'i', 'u', 'size', 'goto', 'pl'],
            Express: function( Content, LabelHead )
            {
                return '<div class="title">' + Content.replace( /\n/g, '' ) + '</div>';
            },
        },
        
        content: {
            Num: 2, InSelf: true, Static: true,
            Express: function( Content, LabelHead )
            {
                return '<div class="content">' + Content + '</div>';
            },
        },
        
        edit: {
            Num: 2, Static: true,
            Express: function( Content, LabelHead )
            {
                return '<br/><br/><div class="editlog">最后编辑于&nbsp;' + Content + '</div>';
            },
        },
        
        toggle: {
            Num: 2, NotIn: ['title', 'url', 'goto', 'pl'], FirstLabel: '[toggle=off]\n[title]标题[/title]\n[content]', note: '隐现器',
            LastLabel: '[/content]', Content: '内容', InSelf: true, NoText: true,
            Express: function( Content, LabelHead )
            {
                //alert( Content );
                var m = LabelHead.match( /^\[toggle=(on|off)\]/i );
                return '<div class="toggle leftborder" data-on="' + m[1] + '">' + Content + '</div>';
            },
        },
        
        table: {
            Num: 2, NoSel: true, NotIn: ['title', 'url', 'goto', 'pl'], NoText: true, note: '表格',
            FirstLabel: '\n[table]\n[tr][td]第一行第一列[/td][td]第一行第二列[/td][/tr]\n[tr][td]第二行第一列[/td][td]第二行第二列[/td][/tr]\n[/table]\n',
            Express: function( Content, LabelHead )
            {
                return '<table class="common" align="center"><tbody>' + Content + '</tbody></table>';
            },
        },
                
        tr: { Num: 2, MustIn: 'table', note: '表格行', },
        td: { Num: 2, MustIn: 'tr', note: '表格行中的列', },
        
        select: {
            Num: 2, NoSel: true, NotIn: ['title', 'url', 'goto', 'pl'], InSelf: true, NoText: true, note: '选择器',
            FirstLabel: '\n[select]\n[choice=on][title]选项名1[/title][content]选项内容1[/content][/choice]\n[choice][title]选项名2[/title][content]选项内容2[/content][/choice]\n[/select]\n',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /^\[select(=([0-2]))?\]/i );
                return '<div class="select" data-mode="' + ( m[2] || '0' ) + '"><div class="head"></div><div class="body">' + Content + '</div></div>';
            },
        },
        
        choice: {
            Num: 2, NoSel: true, MustIn: 'select', InSelf: true, FirstLabel: '[choice][title]选项名[/title][content]选项内容[/content][/choice]', note: '选择器选项',
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /^\[choice(=(on|off))?\]/i );
                return '<div class="choice" data-sel="' + ( m[2] || '0' ) + '">' + Content + '</div>';
            },
        },
        
        a: {
            Num: 1, FirstLabel: '[a=anchorName]', note: '锚标', NotIn: ['url', 'goto', 'pl'],
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /\[a=(.*?)\]/i );
                return '<a name="' + m[1] + '"></a>';
            },
        },
        
        goto: {
            Num: 2, note: '帖内跳转', FirstLabel: '[goto=anchorName]', Content: '这里', NotIn: ['title', 'url', 'pl'],
            Express: function( Content, LabelHead )
            {
                var m = LabelHead.match( /^\[goto=(.*?)\]/i );
                return '<a class="goto" data-anchor="' + m[1] + '">' + Content + '</a>';
            },
        },
    };
    
    
    //**************************************************************************
    var LabelObj = function( Name, Order, Text )
    {
        this.Name = Name;
        //this.Parent = Parent;
        this.Text = Text;
        this.Order = Order;
        this.Order2 = -1;
        this.Closed = false;
        this.Childs = [];
        this.Type = LabelType[Name];
    };
    
    LabelObj.prototype.AddChild = function( child )
    {
        this.Childs.push( child );
        return this.Childs.length;
    };
    
    LabelObj.prototype.Close = function( Order )
    {
        this.Order2 = Order;
        this.Closed = true;
    };
    
    //**************************************************************************
    this.Init = function()
    {
        var LabelProto = {
            
            Insert: function()
            {
                var SelStart = ubb.TextArea[0].selectionStart;
                var SelEnd = ubb.TextArea[0].selectionEnd;
                var Content = ubb.TextArea.val();
                
                var InsertStr = '', InsertStr2 = '';
                
                if( LabelType[this.Name].Num == 2 && !LabelType[this.Name].NoSel )
                {
                    if( this.LastLabel )
                    {
                        InsertStr2 = this.LastLabel + '\n' + '[/' + this.Name + ']';
                    }
                    else
                    {
                        InsertStr2 = '[/' + this.Name + ']';
                    }
                    
                    if( SelStart == SelEnd )
                    {
                        var LbContent = this.Content || '';
                        InsertStr2 = LbContent + InsertStr2;
                    }
                    
                    if( this.NextLn )
                    {
                        InsertStr2 += '\n';
                    }
                    
                    Content = Content.slice( 0, SelEnd ) + InsertStr2 + Content.slice( SelEnd, Content.length );
                }
                
                InsertStr = this.FirstLabel || ( '[' + this.Name + ']' );
                Content = Content.slice( 0, SelStart ) + InsertStr + Content.slice( SelStart, Content.length );
                
                ubb.TextArea.val( Content );
                ubb.TextArea[0].selectionStart = ubb.TextArea[0].selectionEnd = SelEnd + InsertStr.length + InsertStr2.length;
            },
            
            GetStyleStr: function( param )
            {
                var Permits = ['display', 'height', 'width', 'border', 'border-top', 'border-bottom', 'border-left', 'border-right', 
                                'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right', 'background-color',
                                'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right', 'color', 'font-size',
                                'overflow', 'overflow-x', 'overflow-y', 'align', 'valign', 'colspan', ];
                var s = '';
                _( param ).chain().pairs().each( function( p )
                {
                    if( _( Permits ).contains( p[0] ))
                    {
                        s += p.join( ':' ) + ';';
                    }
                } );
                
                return s;
            },
            
            ParseParam: function( PrmStr, DefaultProp )
            {
                var Param = {};
                
                _( PrmStr.split( '|' )).each( function( pairStr, Idx )
                {
                    if( Idx === 0 )
                    {
                        if( pairStr.length > 0 )
                        {
                            Param[DefaultProp] = pairStr;
                        }
                    }
                    else
                    {
                        var kv = pairStr.split( '=' );
                        Param[kv[0]] = kv[1];
                    }
                } );
                
                return Param;
            },
    
            Express: function( Content, LabelHead )
            {
                return '<' + this.Name + '>' + Content + '</' + this.Name + '>';
            },
        };
            
        _( LabelType ).chain().pairs().each( function( p )
        {
            p[1].Name = p[0];
            
            for( var k in LabelProto )
            {
                if( !( k in p[1] ))
                {
                    p[1][k] = LabelProto[k];
                }
            }
        } );
        
        if( !ubb.BtnArea )      //显示时的调用
        {
            return;
        }
        
        if( ubb.TextArea[0].selectionStart === undefined )
        {
            ubb.BtnArea.append( '<div style="color:red">以上为旧式 UBB。<br/>新式 UBB 不支持低版本 IE 内核浏览器。<br/>请改用 '
                        + '<a class="green" href="http://www.mozilla.org/en-US/firefox/fx/" target="_blank">Firefox</a> '
                        + '或 <a class="green" href="http://www.google.com.hk/chrome" target="_blank">Chrome</a> 的最新版本。</div>' );
            return;             //ie
        }
        
        ubb.BtnArea.html( '' );
        
        _( LabelType ).chain().pairs().each( function( p )
        {
            if( p[1].Static )           //隐式标签
            {
                return;
            }
            
            p[1].Btn = $( '<div class="ubbbtn" title="' + p[1].note + '">' + p[0] + '</div>' );
            p[1].Btn.click( function()
            {
                var Html0 = ubb.TextArea.val();
                var Scroll = ubb.TextArea.scrollTop();

                p[1].Insert();
                
                try
                {
                    var Tree = new LabelTree( LabelType, ubb.TextArea.val());
                }
                catch( e )
                {
                    alert( e );
                    //throw e;
                    if( p[0] !== 'r' )
                    {
                        var ErrName = e.split( ',' )[0];
                        if( _( ['LabelNotInErr', 'LabelPairErr', 'LabelMoreInRErr', 'LabelMaxLayerErr', 'LabelMustInErr', 'LabelInSelfErr'] ).contains( ErrName ))
                        {
                            alert( '错误：不能如此插入标签。' );
                            ubb.TextArea.val( Html0 );
                            ubb.TextArea.scrollTop( Scroll );
                            return;
                        }
                    }
                    else
                    {
                        alert( '警告：R 标签屏蔽了双标签中的一个，致另外一个无法配对。' );
                    }
                }
                ubb.TextArea.scrollTop( Scroll );
                ubb.TextArea.focus();
            } );
            
            ubb.BtnArea.append( p[1].Btn );
        } );
        
        //ubb.BtnArea.children( '.ubbbtn' ).css( { border: 'solid #fc0 1px', 'background-color': '#ffc', cursor: 'pointer', 'padding-left': '7px', 'padding-right': '7px', } );
    };

    this.Check = function( text )
    {
        var Tree = new LabelTree( LabelType, text );
        return Tree.Show();
    };
    
    this.GotoTarget = function( Dom, Anch )
    {
        var ObjA = $( 'a[name="' + Anch + '"]', Dom );
        if( ObjA.parent().is( ":visible" ))
        {
            if( ObjA.parent().hasClass( 'selkey' ))    //a 标签放在 selkey 上，触发点击
            {
                ObjA.click();
            }
            else if( ObjA.parent().hasClass( 'title' ) && ObjA.parent().children( 'span' ).html() === '◣' )    //a 标签放在 title 上，触发点击
            {
                ObjA.click();
            }
        }
        else
        {
            ObjA.parents().each( function()
            {
                if( $( this ).hasClass( 'toggle' ))
                {
                    //alert( $( this ).children( '.title' ).children( 'span' ).html());
                    if( $( this ).children( '.title' ).children( 'span' ).html() === '◣' )
                    {
                        $( this ).children( '.title' ).click();
                    }
                }
                else if( $( this ).hasClass( 'choice' ))
                {
                    var i = $( this ).index();
                    $( this ).parent().parent().children( '.head' ).children( '.selkey:eq(' + i + ')' ).click();
                    //alert( $( this ).children( '.title' ).children( 'span' ).html() );
                    if( $( this ).children( '.title' ).children( 'span' ).html() === '◣' )
                    {
                        $( this ).children( '.title' ).click();
                    }
                }
            } );
            //setTimeout( function(){ location.hash = ''; location.hash = Anch; }, 550 );
        }

        $( '#forumpg' ).animate( { scrollTop: Anch.offset().top - 50 }, 600 );
    };
    
    this.Show = function( Dom )
    {
        var Tree = new LabelTree( LabelType, Dom.html());
        Dom.html( Tree.Show());
        
        $( 'a.goto', Dom ).mouseover( function()
        {
            var Anch = $( this ).data( 'anchor' );
            var ObjA = $( 'a[name="' + Anch + '"]', Dom );
            console.log( 'mouseover' );
            ObjA.html( '<span class="target">▶</span>' );
            //ObjA.parent().wrapInner( '<div class="gotoobj"></div>' );
        } );
        
        $( 'a.goto', Dom ).mouseout( function()
        {
            var Anch = $( this ).data( 'anchor' );
            var ObjA = $( 'a[name="' + Anch + '"]', Dom );
            
            ObjA.html( '' );
            //setTimeout( function(){ ObjA.unwrap(); }, 700 );
        } );
        
        $( 'a.goto', Dom ).click( function()            //对跳转目标上级 dom 的处理
        {
            var Anch = $( this ).data( 'anchor' );
            ubb.GotoTarget( Dom, Anch );
        } );
        
        /*$( 'a.goto', Dom ).click( function()
        {
            var Anch = $( this ).data( 'anchor' );
            //location.hash = Anch; 
            //setTimeout( function(){ location.hash = Anch; }, 1000 );
            $( 'a[name="' + Anch + '"]' ).click();
        } );*/
        
        $( 'div.toggle>.title', Dom ).prepend( '<span class="trigger">◤</span>' );
        $( 'div.toggle>.title', Dom ).click( function()
        {
            if( $( '.trigger', $( this )).html() === '◣' )
            {
                $( this ).css( 'display', 'block' );
                $( this ).parent().css( 'display', 'block' );
                $( this ).parent().addClass( 'leftborder' );
                $( this ).next( '.content' ).show( 500 );
                $( this ).children( '.trigger' ).html( '◤' );
            }
            else
            {
                $( this ).css( 'display', 'inline' );
                $( this ).parent().css( 'display', 'inline' );
                $( this ).parent().removeClass( 'leftborder' );
                $( this ).next( '.content' ).hide( 500 );
                $( this ).children( '.trigger' ).html( '◣' );
            }
        } );
        
        $( 'div.toggle', Dom ).each( function()
        {
            if( $( this ).data( 'on' ) !== 'on' )
            {
                $( this ).children( '.title' ).click();
                $( this ).children( '.content' ).hide();
            }
        } );
        
        //$( 'table.common tr', Dom ).css( 'height', '30px' );
        
        $( 'div.select', Dom ).each( function()
        {
            var Sel = $( this );
            var Mode = Sel.data( 'mode' );
            //alert( Boolean( Mode ) + ',' + Mode + ',' + typeof Mode );
            
            if( Mode == 0 )
            {
                var SelKey = null;
                var Choice = Sel.children( '.body' ).children( '.choice' );
                
                Choice.children( '.title' ).each( function( Idx )
                {
                    //alert( Idx );
                    var Span = $( '<span class="selkey"></span>' );
                    Span.append( $( this ).html() );
                    Span.data( 'index', Idx );
                    if( $( this ).parent().data( 'sel' ) === 'on' )
                    {
                        SelKey = Span;
                        Span.data( 'sel', 'on' );
                    }
                    Sel.children( '.head' ).append( Span );
                    $( this ).remove();
                } );
                
                Sel.children( '.head' ).children( '.selkey' ).click( function()
                {
                    Choice.children( '.content' ).hide();
                    Choice.children( '.content:eq(' + $( this ).data( 'index' ) + ')' ).show( 500 );
                    Sel.children( '.head' ).children( '.selkey' ).css( 'background-color', '' );
                    $( this ).css( 'background-color', '#ffcc22' );
                } );
                
                Choice.children( '.content' ).hide();
                
                if( SelKey )
                {
                    SelKey.click();
                }
            }
            else if( Mode == 1 )
            {
                var Choice = Sel.children( '.body' ).children( '.choice' );
                
                Choice.children( '.title' ).prepend( '<span class="trigger">◣</span>' );
                Choice.children( '.title' ).click( function()
                {
                    if( $( this ).children( '.trigger' ).html() === '◣' )
                    {
                        Choice.children( '.content' ).hide( 500 );
                        Choice.removeClass( 'leftborder' );
                        Choice.children( '.title' ).children( '.trigger' ).html( '◣' );
                        
                        $( this ).parent().addClass( 'leftborder' );
                        $( this ).parent().children( '.content' ).show( 500 );
                        $( this ).children( '.trigger' ).html( '◤' );
                    }
                    else
                    {
                        $( this ).parent().removeClass( 'leftborder' );
                        $( this ).parent().children( '.content' ).hide( 500 );
                        $( this ).children( '.trigger' ).html( '◣' );
                    }
                } );
                
                Sel.children( '.head' ).remove();
                $( '.content', Sel ).hide();
                Sel.children( '.body' ).children( '.choice[data-sel=on]' ).children( '.title' ).click();
            }
            else if( Mode == 2 )
            {
                var SelFrame = null;
                
                $( '.head', Sel ).html( '<button class="prev">﹤</button><button class="play">▷</button><button class="next">﹥</button>' );
                $( '.title', Sel ).remove();
                $( '.choice', Sel ).hide();
                SelFrame = $( '.choice:first', Sel );
                SelFrame.show();
                
                Sel.TurnNext = function()
                {
                    SelFrame.hide( 100 );
                    if( SelFrame.next( '.choice' ).length > 0 )
                    {
                        SelFrame = SelFrame.next( '.choice' );
                    }
                    else
                    {
                        SelFrame = $( '.choice:first', Sel );
                    }
                    SelFrame.show( 100 );
                };
                
                $( '.next', Sel ).click( Sel.TurnNext );
                
                $( '.prev', Sel ).click( function()
                {
                    SelFrame.hide();
                    if( SelFrame.prev( '.choice' ).length > 0 )
                    {
                        SelFrame = SelFrame.prev( '.choice' );
                    }
                    else
                    {
                        SelFrame = $( '.choice:last', Sel );
                    }
                    SelFrame.show();
                } );
                
                Sel.Play = function()
                {
                    if( $( '.play', Sel ).data( 'playing' ) === 'on' )
                    {
                        Sel.TurnNext();
                        
                        setTimeout( Sel.Play, 1000 );
                    }
                };
                
                $( '.play', Sel ).click( function()
                {
                    if( $( this ).data( 'playing' ) === 'on' )
                    {
                        $( this ).html( '▷' );
                        $( this ).data( 'playing', '' );
                    }
                    else
                    {
                        $( this ).html( '□' );
                        $( this ).data( 'playing', 'on' );
                        Sel.Play();
                    }
                } );
            }
        } );
    };
    
    this.ChkLabelSel = function( lbObj )
    {
        var Sel = window.getSelection();
        var Range = Sel.getRangeAt( 0 );
        return Range
    };
    
    this.Init();
}
