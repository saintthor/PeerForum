var Input = function( tr, parentId, protoId, submitFunc )
{
	var input = this;

	this.TR = tr;
	this.IsRoot = !parentId;
	this.IsEdit = !!protoId;
	this.ParentId = parentId;
	this.ProtoId = protoId;
	this.SubmitFunc = submitFunc;

	this.GetInputContent = function()
	{
		var Content = $( 'textarea', input.TR ).val();
		try
		{
			input.UBB.Check( Content );
		}
		catch( e )
		{
			alert( 'UBB　标签错误，请改正后再提交。' );
			return;
		}

		if( $( ':checkbox', input.TR ).prop( 'checked' ))
		{
			Content = _( Content.split( '\n' )).chain().map( function( ln )
			{
				return ln.replace( /^\s+|\s+$/g, '' );
			} ).filter( function( ln )
			{
				return ln > '';
			} ).value().join( '\n\n' );
		}

		if( Content.length < 1 )
		{
			$( '.note', input.TR ).html( '帖子不能为空。' );
			return;
		}

		if( this.IsRoot && Content.length < 20 )
		{
			$( '.note', input.TR ).html( '根帖内容不能少于 20 字。' );
			return;
		}

		return Content;
	};

	this.Draw = function()
	{
		this.TR.html( '<td class="ubbbtns" width="150px"></td><td class="tpctd"> \
			<textarea name="article" rows="16" cols="100" style="overflow:auto; width:98%;" \
			 placeholder="在此输入帖子内容。第一行为标题。"></textarea><br/> \
			 <input type="checkbox" checked=true/>自动排版<span class="query" title="">？</span> \
			 <span class="vice">先</span><button class="preview"> 预 览 </button><span class="vice">再</span><button class="post"> 提 交 </button> \
			 <div class="note"/><div class="previewarea"/></td>' );

		if( this.IsRoot )
		{
			$( 'span.vice:first', this.TR ).before( '<select><option value=0>永久保存</option> \
				<option value=10>保存 10 日</option><option value=50>保存 50 日</option> \
				<option value=200>保存 200 日</option><option value=1000>保存 1000 日</option> \
				</select><input type="text" style="width:115px" placeholder="固有标签，逗号分隔。"/>' );
		}

		QueryPop( this.TR.children( 'td' ).children( '.query' ), 'autoedit' );
		this.UBB = new UBBObj( this.TR.children( 'td.ubbbtns' ), $( 'textarea', this.TR ));
		//this.TR.children( 'td.ubbbtns' ).append( '<span class="query" title="">？</span>' )
		//QueryPop( this.TR.children( 'td.ubbbtns' ).children( '.query' ), 'ubb' );
		this.TR.children( 'td.ubbbtns' ).append( '<div class="ubbnote">通过 UBB 标签为帖子提供一些格式及动态效果。标签功能依照 guideep 的标准实现，详细使用说明请看<a href="http://www.guideep.com/read?guide=5715999101812736#ubbwidget" target="_blank">《guideep 教程编辑指南》中有关 UBB 的部分</a>。</div>' );

		$( 'button.preview', this.TR ).click( function()
		{
			var Preview = $( '.previewarea', this.TR );
			if( Preview.html())
			{
				Preview.html( '' );
				Preview.hide( 200 );
				return;
			}
			var Content = input.GetInputContent();

			Preview.html( Content.replace( /\&/g, '&amp;' ).replace( / /g, '&nbsp;&nbsp;' ).replace( /\>/g, '&gt;' ).replace( /\</g, '&lt;' ).replace( /\n/g, '<br/>' ));
			//atclbody.html( frm.ShowContent( atcl.content ));
			var UBB = new UBBObj();
			UBB.Show( Preview );
			Preview.show( 300 );
			$( this ).next( 'button' ).attr( 'disabled', false );
		} );

		$( 'button.post', this.TR ).attr( 'disabled', true );

		$( 'button.post', this.TR ).click( function()
		{
			$( '.note', input.TR ).html( '' );
			var Content = input.GetInputContent();

			if( input.IsRoot )
			{
				var AtclLabels = $( ':text', input.TR ).val()

				//console.log( AtclLabels );
				if( !AtclLabels )
				{
					$( '.note', input.TR ).html( '标签不能为空。' );
					return;
				}

				var AtclData = {
					'cmd': 'NewTopic',
					'content': Content,
					'Labels': AtclLabels,
					'life': 86400000 * $( '.tpctd>select' ).children( 'option:selected' ).val(),
								};
			}
			else	//is reply
			{
				var AtclData = {
					'cmd': 'Reply',
					'parent': input.ParentId,
					'content': Content,
								};
			}
			console.log( AtclData );

			input.SubmitFunc( AtclData );
		} );
	};

	this.Draw();
};

function QueryPop( dom, k )
{
	dom.mouseover( function()
	{
		var html = {
			'views': '三种视图，是在一个话题里排列帖子的三种不同方式。<br>流视图是像一般的论坛那样，将话题里的所有帖子按时间排列显示，不表达帖子间的回复关系。<br>链视图与星视图分别选取话题中与当前帖子相关的上级或下级帖子，用于在庞大的帖子树里，快速呈现自己关心的部分。<br>一个帖子的链视图是此帖的所有上级帖子的集合，是从这个帖子向上追溯到根帖的回复路径。当前帖子在最下，根帖在最上。<br>一个帖子的星视图是此帖的所有下级帖子的集合，当前帖子在最上，下面是直接回复它的帖子，再下面是回复那些回复帖的帖子，逐层排列。',
			'manage': '在飘上，没有管理员。每一位用户都是自己节点的管理员，有权决定自己的节点上有哪些帖子可以被邻节点读取。<br>无论一个帖子是从邻节点读到还是在本节点发布的，它的初始状态都是“未裁处”，你可以对它执行阻断、放行、推荐三种裁处。<br>未裁处的帖子被完整显示时会开始一分钟的倒计时，计时结束后被自动放行。<br>已阻断、已通过、已推荐的帖子也可以重新裁处，但不能恢复到未裁处状态。<br>只有已放行或已推荐的帖子可被邻节点读取，未裁处和已阻断的帖子不可被读取。<br>邻节点也可以选择只取经过推荐的帖子，不取仅被放行的帖子。<br>每个节点对外提供的内容等若节点及用户的名片。当邻节点推荐了一个从你这里读取的帖子，它对你的评级会上升；当它阻断来自你的帖子，它对你的评级会下降。评级指示了一个节点对另一个节点的认同程度，节点会优先从评级较高的邻节点获取内容。<br>飘的和谐与自由仰赖每一位用户的公正裁处。用户有责任阻断那些粗鄙、恶毒、蛮横、虚假、庸俗的帖子，放行及推荐那些理性、精辟、高雅、真诚、优美的帖子，将好的传给他人。<br>你为他人所做，也是他人为你所做的。',
			'userpubk': '飘没有用户系统，不同的用户可能有相同的用户名，因此，需要以用户公钥来区分用户。用鼠标指向用户名可见用户公钥，公钥很长，不好认，从公钥生成一个 RandomArt，就是下面这个字符组成的小图，就容易识别了。用户公钥（RandomArt）相同就是同一个人，用户名是随时可以改的。',
			'autoedit': '选中自动排版，会在提交时去掉内容中每一段前后的空格，并在段与段之间插入一个空行。<br/>如果帖子里含有程序代码之类对格式要求严格的内容，不应选中自动排版。',
			//'ubb': 'UBB 标签用于在帖子中实现一些格式和动态效果。这些标签依照 guideep 的标准实现，详细使用说明请看<a href="http://www.guideep.com/read?guide=5715999101812736#ubbwidget" target="_blank">《guideep 教程编辑指南》中有关 UBB 的部分</a>。',
			'label': '飘上的话题依照标签划分门类或圈子。标签分为固有标签与节点标签两种。<br>固有标签是作者创建话题时设定的，发布之后不可更改。而每个节点的用户有权对话题增加一些标签，或者屏蔽一些固有标签，新增的就是节点标签。<br>节点标签只在当前节点上有效。如果邻节点按照标签来读取话题，（未屏蔽的）固有标签与节点标签同样有效。但邻节点取得话题之后，前一节点对固有标签的屏蔽不再生效，话题的固有标签仍然完整。',
		}[k];

		var PopDiv = $( '<div class="pop">' + html + '</div>' );
		$( this ).append( PopDiv );
		PopDiv.css( 'top', $( this ).offset().top + parseInt( $( this ).css( 'height' )) + 'px' );

		var WndRight = $( window ).width();
		//console.log( WndRight, PopDiv.offset().left, parseInt( PopDiv.css( 'width' )));
		if( PopDiv.offset().left + parseInt( PopDiv.css( 'width' )) > WndRight )
		{
			//console.log( WndRight - parseInt( PopDiv.css( 'width' )) + 'px' );
			PopDiv.css( 'left', WndRight - parseInt( PopDiv.css( 'width' )) - 40 + 'px' );
		}
		PopDiv.children( 'a' ).click( function()
		{
			console.log( 'a clicked.' );
		} );
		PopDiv.click( function()
		{
			console.log( 'pop clicked.' );
		} );
	} );

	dom.mouseleave( function()
	{
		$( this ).children( '.pop' ).remove();
	} );
}

var Passer = function( bodyDiv, passFunc )
{
	var passer = this;
	this.BodyDiv = bodyDiv;
	this.PassFunc = passFunc;

	this.Second = 60;
	this.HeadShowed = false;
	this.FootShowed = false;

	this.Check = function()
	{
		//console.log( this.BodyDiv.offset().top, $( window ).scrollTop(), this.BodyDiv.offset().height );
		this.HeadShowed = this.HeadShowed || this.Inscreen( this.BodyDiv.offset().top );
		this.FootShowed = this.FootShowed || this.Inscreen( this.BodyDiv.offset().top + parseInt( this.BodyDiv.css( 'height' )));
		//console.log( this.BodyDiv.offset().top, this.HeadShowed, this.FootShowed );
		if( this.HeadShowed && this.FootShowed )
		{
			var Btn = $( 'button.pass', this.BodyDiv.siblings( 'div.atclfoot' ));
			if( Btn.children( 'span' ).length == 0 )
			{
				var TimerSpan = $( '<span class="timer"></span>' );
				Btn.append( TimerSpan );
				this.Timeing( TimerSpan );
			}
		}
	};

	this.Finished = function()
	{
		return this.Second <= 0;
	};

	this.Inscreen = function( y )
	{
		var top = $( window ).scrollTop();
		var bottom = top + $( window ).height();
		//console.log( y, top, bottom );
		return y >= top && y <= bottom;
	};

	this.Timeing = function( dom )
	{
		if( --this.Second > 0 )
		{
			setTimeout( function(){ passer.Timeing( dom ); }, 1000 );
			dom.html( this.Second );
		}
		else
		{
			//this.PassFunc();
			dom.parent().remove();
		}
	};
}

var Forum = function( owner )
{
	var frm = this;

	this.FLOWMODE = 0;
	this.LINKMODE = 1;
	this.STARMODE = 2;

	this.TITLELEN = 99;
	this.PASSTIME = 60;

	this.Owner = owner;
	this.StartPos = 0;
	this.ListLabel = '';
	this.SortCol = 'LastTime';
	this.TopicObj = { 'TreeRoots': {}, 'AutoPasser': {} };

	this.Init = function()
	{
		$( '#newtpcbtn' ).click( function()
		{
			//alert( 'ssssss' );
			$( '#tpcinput' ).toggle( 350 );
			if( $( '#tpcinput td' ).length == 0 )
			{
				new Input( $( '#tpcinput tr' ), null, null, function( data )
				{
					frm.Owner.Post( data, 'GetResult' );
				} );
			}
		} );

		$( '#firstth' ).click( function()
		{
			frm.SortCol = 'FirstTime';
			frm.StartPos = 0;
			$( '#lastth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#lastth' ).click( function()
		{
			frm.SortCol = 'LastTime';
			frm.StartPos = 0;
			$( '#firstth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#returntolist' ).click( function()
		{
			$( '#atclpg' ).hide( 200 );
			$( '#listpg' ).show( 300 );
			$( '#listpg' ).after( $( '#atclpg' ));
		} );

		$( '#forumpg' ).scroll( function()
		{
			frm.ChkPass();
		} );
	};

	this.SetClickTitle = function( dom )
	{
		$( 'span.title', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			//console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'flow' }, 'GetResult' );
		} );
	};

	this.SetClickLastTime = function( dom )
	{
		$( 'span.lasttime', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			//console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'last' }, 'GetResult' );
		} );
	};
	
	this.SetClickArrow = function( dom )
	{
		$( 'span.arrow', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			if( $( this ).text() == '◣' )
			{
				frm.Owner.Post( { cmd: 'GetAtclTree', root: Root, mode: 'tree' }, 'GetResult' );
				$( this ).html( '◤' );
				$( this ).attr( 'title', '降维' );
			}
			else
			{
				$( '#Tree_' + Root ).hide( 400, function()
					{
						$( this ).remove();
					} );
				$( this ).html( '◣' );
				$( this ).attr( 'title', '升维' );
			}
		} );
	};

	this.SetAttr = function( dom )
	{
		this.SetClickTitle( dom );
		this.SetClickLastTime( dom );
		this.SetClickArrow( dom );

		setTimeout( function(){ dom.removeClass( 'new' ); }, 2000 );
	};
	
	this.ShowContent = function( c )
	{
		return c.replace( /\&/g, '&amp;' ).replace( / /g, '&nbsp;&nbsp;' ).replace( /\>/g, '&gt;' ).replace( /\</g, '&lt;' ).replace( /\n/g, '<br/>' );
	};

	this.ChkContentVisible = function( atclbody, authStatus, atcl )
	{
		if( authStatus >= 0 && atcl.status >= 0 )
		{
			atclbody.html( frm.ShowContent( atcl.content ));
			var UBB = new UBBObj();
			UBB.Show( atclbody );
		}
		else
		{
			var info = atcl.status < 0 ? '因帖子被阻断内容不可见。' : '因用户被屏蔽内容不可见。';
			atclbody.html( info + '<button>点此查看</button>' );
			atclbody.children( 'button' ).click( function()
			{
				$( this ).parent().html( frm.ShowContent( atcl.content ));
				var UBB = new UBBObj();
				UBB.Show( atclbody );
			} );
		}
	};

	this.SetLabelStr = function( labelData )
	{
		_( labelData ).chain().pairs().each( function( p )
		{
			frm.TopicObj[p[0]].Labels = p[1];
		} );
	};

	var DelLabelFunc = function()
	{
		var LabelSpan = $( this ).parent();
		var RootId = $( this ).closest( '.tree' ).data( 'root' ) || $( '#atclarea' ).data( 'root' );
		$( this ).remove();
		frm.Owner.Post( {
				cmd: 'DelLabel',
				rootId: RootId,
				label: LabelSpan.html(),
						}, 'GetResult' )
		LabelSpan.hide( 400, function()
		{
			LabelSpan.remove();
		} );
	};

	this.ShowSingleAtcl = function( atclData )
	{
		console.log( atclData );
		var AtclDiv = $( '<div class="atcl" id="Atcl_' + atclData[0] + '"><table><tbody><tr> \
			<td class="atclleft"><div class="nickname"/><span class="query" title="">？</span>\
			<div class="randomart"></div> \
			<div class="manageuser"></div></td><td class="atclright"><div class="atcltop"> \
			<span class="lineright"><span class="flow" title="流视图">流</span> \
			<span class="link" title="链视图">链</span> \
			<span class="star" title="星视图">星</span><span class="query" title="">？</span></span> \
			<span class="time"></span><span class="linemiddle"> \
			<span class="bigger" title="放大帖子正文">大</span><span class="smaller" title="缩小帖子正文">小</span> \
			</span></div><div class="atclid"></div> \
			<span class="labels lineright"></span><div class="atclbody"></div> \
			<div class="atclfoot"><span class="manage"></span><span class="lineright"> \
			<!--button class="edit">编辑</button--><button class="reply">回复</button></span></div> \
			</td></tr></tbody></table><div></div></div>' );

		var AuthPubKey = atclData[1].AuthPubKey;
		var AuthStatus = frm.Owner.ChkAuthStatus( AuthPubKey );
		var NameDiv = $( '.nickname', AtclDiv );

		NameDiv.html( atclData[1].NickName );
		NameDiv.attr( 'title', '用户公钥：' + AuthPubKey );

		this.ChkContentVisible( $( '.atclbody', AtclDiv ), AuthStatus, atclData[1] );
		this.SetManageBtns( $( '.manage', AtclDiv ), atclData[1].status );

		if( atclData[1].status == 0 )
		{
			frm.TopicObj.AutoPasser[atclData[0]] = new Passer( $( '.atclbody', AtclDiv ), function()
			{
				frm.Manage( atclData[1], 'pass' );
			} );
		}

		$( '.randomart', AtclDiv ).html( frm.RandomArt( str_md5( AuthPubKey )));
		$( '.time', AtclDiv ).html( frm.ShowTime( atclData[1].CreateTime ));
		if( atclData[1].DestroyTime < atclData[1].CreateTime + 10000 * 1000 * 86400 )
		{
			var DestroyTime = $( '<div class="destroytime" title="失效时间">~' + this.ShowTime( atclData[1].DestroyTime ) + '</div>' );
			$( '.atclbody', AtclDiv ).after( DestroyTime );
		}
		$( '.atclid', AtclDiv ).html( atclData[0] );
		//$( '.likenum', AtclDiv ).html(( atclData[1][0].Liked || [] ).length );
		$( '.atclfoot', AtclDiv ).data( 'atclid', atclData[0] );

		if( atclData[1].LabelStr )
		{
			console.log( atclData[1].LabelStr );
			var LabelDiv = $( '.labels', AtclDiv );
			var RootId = LabelDiv.closest( '.tree' ).data( 'root' ) || $( '#atclarea' ).data( 'root' );
			_( atclData[1].LabelStr.split( '|' )).each( function( lbstr, i )
			{
				console.log( lbstr, i );
				if( lbstr )
				{
					_( lbstr.split( ',' )).each( function( label )
					{
						if( label )
						{
							var LbClass = ['staticlabel', 'nodelabel'][i];
							var LbTitle = ['屏蔽固有标签', '删除节点标签'][i]
							LabelDiv.append( '<span class="' + LbClass + '">' + label 
											+ '<span title="' + LbTitle + '">×</span></span>' );
						}
					} );
				}
			} );
			LabelDiv.append( '<div class="addlabel"><input type="text" placeholder="添加节点标签" width=30px;/> \
							<button>+</button><span class="query" title="">？</span></div>' );
			LabelDiv.mouseover( function()
			{
				LabelDiv.children( '.addlabel' ).show();
			} );
			LabelDiv.mouseleave( function()
			{
				LabelDiv.children( '.addlabel' ).hide();
			} );
			LabelDiv.children( 'span' ).children( 'span' ).click( DelLabelFunc );

			QueryPop( $( '.query', LabelDiv ), 'label' );

			$( 'button', LabelDiv ).click( function()
			{
				var NewLabel = $( this ).siblings( ':text' ).val();
				console.log( NewLabel );
				if( NewLabel )
				{
					frm.Owner.Post( {
							cmd: 'AddLabel',
							rootId: RootId,
							label: NewLabel,
									}, 'GetResult' )
					var NewLabelSpan = $( '<span class="nodelabel">' + NewLabel 
								+ '<span title="删除节点标签">×</span></span>' );
					$( this ).parent().before( NewLabelSpan );
					NewLabelSpan.children( 'span' ).click( DelLabelFunc );
				}
			} );
		}

		if( AuthPubKey != frm.Owner.CurUser[0] )
		{
			$( '.edit', AtclDiv ).remove();
			$( '.manageuser', AtclDiv ).append( AuthStatus >= 0 ? '<button class="blockbtn">屏蔽</button>' : '<button class="unblockbtn">解除屏蔽</button>' );
			$( '.manageuser', AtclDiv ).append( AuthStatus <= 0 ? '<button class="followbtn">关注</button>' : '<button class="unfollowbtn">取消关注</button>' );
		}

		return AtclDiv;
	};

	this.GetSetStatusBtns = function( status )
	{
		return {
			0: '<button class="pass">放行</button><button class="commend">推荐</button>',
			1: '<button class="block">阻断</button><button class="pass">放行</button><button class="commend">推荐</button>',
			2: '<button class="block">阻断</button><button class="commend">推荐</button>',
			3: '<button class="block">阻断</button><button class="uncommend">取消推荐</button>',
				}[status + 1];
	};

	this.SetManageBtns = function( dom, status )
	{
		//console.log( dom, status );
		dom.html( this.GetSetStatusBtns( status ));
		dom.append( '<span class="query" title="">？</span>' );
		QueryPop( dom.children( '.query' ), 'manage' );

		[
			['.commend', '推荐这个帖子，以使其他节点优先读取。'],
			['.uncommend', '取消推荐，将帖子置为放行状态。'],
			['.block', '阻断这个帖子，禁止其他节点读取。' ],
			['.pass', '放行这个帖子，以使其他节点能够读取。'],
		].forEach( function( btnTitle )
		{
			dom.children( btnTitle[0] ).attr( 'title', btnTitle[1] );
		} );
	};

	var SetView = function()
	{
		var AtclId = $( this ).closest( 'td' ).children( '.atclfoot' ).data( 'atclid' );
		var RootId = $( this ).closest( '.tree' ).data( 'root' ) || $( '#atclarea' ).data( 'root' );
		var Mode = {
			'flow': frm.FLOWMODE,
			'link': frm.LINKMODE,
			'star': frm.STARMODE,
					}[$( this ).attr( 'class' )];
		frm.ShowAtcls( RootId, Mode, AtclId)
	};

	var SetSize = function()
	{
		var Body = $( this ).closest( 'td' ).children( '.atclbody' );
		var size = parseFloat( Body.css( "font-size" ), 10 );
		var diff = $( this ).hasClass( 'bigger' ) ? 2: -2;
		size += diff;
		Body.css( "font-size", size + 'px' );
		Body.css( "line-height", size * 1.5 + "px" );				
	};

	var EnableReply = function()
	{
		var TBody = $( this ).closest( 'tbody' );
		if( TBody.children( 'tr.input' ).length > 0 )
		{
			TBody.children( 'tr.input' ).toggle( 300 );
			return;
		}
		var TR = $( '<tr class="input"></tr>' );
		//console.log( )
		var RootId = $( this ).closest( '.tree' ).data( 'root' ) || $( '#atclarea' ).data( 'root' );

		console.log( $( this ).closest( '.atclfoot' ).data( 'atclid' ));
		new Input( TR, $( this ).closest( '.atclfoot' ).data( 'atclid' ), null, function( data )
		{
			data.root = RootId;
			frm.Owner.Post( data, 'GetResult' );
		} );

		TR.hide();
		TBody.append( TR );
		TR.show( 400 );
	};

	this.SetTopicData = function( treeData )
	{
		var Tree = this.TopicObj[treeData[0]] = _( treeData[1] ).omit( function( v, k )
		{
			return v.Type == 1;
		} );

		var Roots = [treeData[0]];

		_( Tree ).chain().pairs().sortBy( function( p )
		{
			return p[1].CreateTime;
		} ).each( function( p )
		{
			var ParentId = p[1].ParentID;
			if( !ParentId )
			{
				return;
			}
			var Parent = Tree[ParentId]
			if( Parent )
			{
				Parent.Children = Parent.Children || [];
				Parent.Children.push( p[0] );
			}
			else
			{
				Roots.push( ParentId );
			}
		} );

		this.TopicObj.TreeRoots[treeData[0]] = Roots;
	};

	this.FlowModeAtcls = function( rootId )
	{
		return _( this.TopicObj[rootId] ).chain().pairs().sortBy( function( p )
				{
					return p[1].CreateTime;
				} );
	};

	this.LinkModeAtcls = function( rootId, atclId )
	{
		var Topic = this.TopicObj[rootId];
		var Atcl = Topic[atclId]
		var Atcls = [];

		while( Atcl )
		{
			Atcls.push( [atclId, Atcl] );
			atclId = Atcl.ParentID;
			Atcl = Topic[atclId]
		}

		return _( Atcls ).chain().reverse();
	};

	this.StarModeAtcls = function( rootId, atclId )
	{
		var Topic = this.TopicObj[rootId];
		var Atcls = [[atclId, Topic[atclId]]];
		var start = 0;
		var end = 1;

		while( start < end )
		{
			console.log( start, end );
			_( Atcls.slice( start, end )).each( function( parent )
			{
				_( parent[1].Children || [] ).each( function( ch )
				{
					var Child = Topic[ch];
					if( Child )
					{
						Atcls.push( [ch, Child] );
					}
				} );
			} );
			start = end;
			end = Atcls.length;
		}
		return _( Atcls );
	};

	this.ShowAtcls = function( rootId, mode, atclId )
	{
		$( '#listpg' ).hide( 200 );
		$( '#atclpg' ).show( 300 );
		$( '#atclpg' ).after( $( '#listpg' ));
		$( '#atclarea' ).html( '' );
		$( '#atclarea' ).data( 'root', rootId );
		
		var Atcls = this[[
				'FlowModeAtcls', 
				'LinkModeAtcls', 
				'StarModeAtcls',
					][mode]]( rootId, atclId );

		Atcls.each( function( p )
		{
			//console.log( p );
			$( '#atclarea' ).append( frm.ShowSingleAtcl( p ));
		} );

		//var ScrTop = $( '#shapestep' ).scrollTop();
		//$( '#atclarea' ).animate( { scrollTop: 2000 }, 200 );
        /*    var Width = $( '#likebtn' ).closest( '.col-lg-2' ).outerWidth() + 13 + 'px';
            var Height = document.documentElement.clientHeight - 20 + 'px'
                $( '#commentface' ).css( 'top', $( this ).offset().top - $( '#commentarea' ).offset().top + 'px' );
                $( this ).css( 'top', $( '#footer' ).offset().top - $( '#commentarea' ).offset().top + 7 * MissDisc++ + 'px' );
        var HisHeight = parseInt( $( '#editline' ).css( 'height' )) - parseInt( $( '#labels' ).css( 'height' )) - parseInt( $( '#pickitem' ).css( 'height' )) - 10 + 'px';
		*/
		if( mode == 1 )
		{
			$( '#forumpg' ).animate( { scrollTop: 2000 }, 1000 );
		}

		QueryPop( $( '#atclarea .atclleft .query' ), 'userpubk' );
		QueryPop( $( '#atclarea .atcltop .query' ), 'views' );

		$( '#atclarea .atcltop>.linemiddle>span' ).click( SetSize );
		$( '#atclarea .atcltop>.lineright>span' ).click( SetView );
		$( '#atclarea .reply' ).click( EnableReply );

		this.SetClickManage( $( '#atclarea .manage' ));
		this.ChkPass();
	};

	this.ChkPass = function()
	{
		//console.log( this.TopicObj.AutoPasser );
		_( this.TopicObj.AutoPasser ).chain().pairs().each( function( p )
		{
			if( p[1].Finished())
			{
				delete frm.TopicObj.AutoPasser[p[0]];
			}
			else
			{
				p[1].Check();
			}
		} );
	};

	this.SetClickTreeTitle = function( root, TR )
	{
		console.log( 'SetClickTreeTitle' );
		var AtclId = TR.data( 'atclid' );
		$( '.title', TR ).click( function()
		{
			frm.ShowAtcls( root, frm.STARMODE, AtclId );
		} );
	};

	this.SetClickTreeLastTime = function( root, TR )
	{
		console.log( 'SetClickTreeLastTime' );
		var AtclId = TR.data( 'atclid' );
		$( 'td:eq(4)', TR ).click( function()
		{
			frm.ShowAtcls( root, frm.LINKMODE, AtclId );
		} );
	};

	this.SetClickTreeArrow = function( root, TR )
	{
		console.log( 'SetClickTreeArrow' );
		var AtclId = TR.data( 'atclid' );
		var Atcl = this.TopicObj[root][AtclId];

		$( '.arrow', TR ).click( function()
		{
			if( $( this ).text() == '◣' )
			{
				var AppendAtcl = $( '<tr id="Append_' + AtclId + '"><td colspan=5></td></tr>' );

				AppendAtcl.children( 'td' ).append( frm.ShowSingleAtcl( [AtclId, Atcl] ));
				QueryPop( $( '.atclleft .query', AppendAtcl ), 'userpubk' );
				$( '.atcltop>.lineright>span', AppendAtcl ).click( SetView );
				$( '.reply', AppendAtcl ).click( EnableReply );

				TR.after( AppendAtcl );
				frm.ChkPass();
				$( this ).html( '◤' );
				$( this ).attr( 'title', '降维' );
			}
			else
			{
				$( '#Append_' + AtclId ).hide( 400, function()
					{
						$( this ).remove();
					} );
				$( this ).html( '◣' );
				$( this ).attr( 'title', '升维' );
			}
		} );
	};

	this.SetClickTreePrefix = function( root, TR )
	{
		console.log( 'SetClickTreePrefix' );
		var AtclId = TR.data( 'atclid' );
		var Atcl = this.TopicObj[root][AtclId];

		$( 'td:eq(1)>span:eq(0)', TR ).click( function()
		{
			if( $( this ).parent().children( '.setstatus' ).length > 0 )
			{
				$( this ).parent().children( '.setstatus' ).remove();
			}
			else
			{
				var SetStatus = $( '<div class="setstatus"></div>' );
				frm.SetManageBtns( SetStatus, Atcl.status );
				SetStatus.append( '<span class="remove" title="取消">×</span>' );
				SetStatus.children( '.remove' ).click( function()
				{
					SetStatus.remove();
				} );
				frm.SetClickManage( SetStatus, Atcl );
				$( this ).after( SetStatus );
			}
		} );
	};

	this.SetTreeLineAttr = function( root, trLnTR )
	{
		this.SetClickTreeTitle( root, trLnTR );
		this.SetClickTreeLastTime( root, trLnTR );
		this.SetClickTreeArrow( root, trLnTR );		
		this.SetClickTreePrefix( root, trLnTR );		
	};

	this.SetClickManage = function( dom, atcl )
	{
		$( 'button', dom ).click( function()
		{
			if( !atcl )
			{
				var RootId = $( this ).closest( '#atclarea' ).data( 'root' );
				var AtclId = $( this ).closest( '.atclfoot' ).data( 'atclid' );
				console.log( RootId, AtclId );
				atcl = frm.TopicObj[RootId][AtclId];
			}

			frm.Manage( atcl, $( this ).attr( 'class' ));
			frm.ReDrawAtcl( $( this ).closest( 'td' ), atcl );
		} );
	};

	this.Manage = function( atcl, act )
	{
		atcl.status = {
				'pass': 1,
				'commend': 2,
				'block': -1,
				'uncommend': 1,
						}[act];

		this.Owner.Post( {
				cmd: 'SetStatus',
				atclId: atcl.atclId,
				status: atcl.status,
						}, 'GetResult' );
	};

	this.ReDrawAtcl = function( TD, atcl )
	{
		if( TD.parent().hasClass( 'treeview' ))
		{
			var PrfInfo = {
					0: ['prfblocked', '已阻断'],
					1: ['prfunread', '未裁处'],
					2: ['prfpassed', '已通过'],
					3: ['prfcommended', '已推荐'],
							}[atcl.status + 1];

			var Prefix = TD.children( 'span:eq(0)' );
			Prefix.removeClass();
			Prefix.addClass( PrfInfo[0] );
			Prefix.attr( 'title', PrfInfo[1] );
			$( '.setstatus', TD ).remove();
		}
		else
		{
			this.SetManageBtns( $( '.manage', TD ), atcl.status );
			this.SetClickManage( $( '.manage', TD ), atcl );
		}
	};

	this.ShowTree = function( rootId )
	{
		console.log( 'ShowTree' );
		var TR = $( '<tr class="tree" id="Tree_' + rootId + '"><td colspan=4><table><tbody></tbody></table></td></tr>' );

		_( this.TopicObj.TreeRoots[rootId] ).each( function( r )
		{
			frm.DrawTreeLine( rootId, r, $( 'tbody', TR ), 0 );
		} );

		TR.data( 'root', rootId );

		$( 'tr', TR ).each( function()
		{
			frm.SetTreeLineAttr( rootId, $( this ));
		} );

		return TR;
	};

	this.DrawTreeLine = function( rootId, parentId, tbody, layer )
	{
		//console.log( rootId, parentId, layer );
		var Parent = this.TopicObj[rootId][parentId];
		if( !Parent )
		{
			return;
		}
		//console.log( Parent );
		var TreeLine = $( '<tr class="treeview"><td><span class="arrow">◣</span></td> \
			<td title="进入本帖星视图"></td><td></td><td></td><td title="进入本帖链视图"><span class="lasttime"></span></td></tr>' );
		TreeLine.data( 'atclid', parentId );
		TreeLine.children( 'td:eq(1)' ).css( 'padding-left', ( layer * 7 ) + 'px' );
		var Prefix = $( '<span>' + ( rootId == parentId ? '●' : layer == 0 ? '◇' : '◆' ) + '</span>' );
		var PrfInfo = {
				0: ['prfblocked', '已阻断'],
				1: ['prfunread', '未裁处'],
				2: ['prfpassed', '已通过'],
				3: ['prfcommended', '已推荐'],
						}[Parent.status + 1];
		Prefix.addClass( PrfInfo[0] );
		Prefix.attr( 'title', PrfInfo[1] );

		var TitleTD = TreeLine.children( 'td:eq(1)' );
		TitleTD.html( '</span><span class="title">' + Parent.content.slice( 0, this.TITLELEN ) + '</span>' );
		if( this.TITLELEN >= Parent.content.length )
		{
			TitleTD.append( '<span class="eof">▓ </span>' );
		}
		TitleTD.prepend( Prefix );
		TreeLine.children( 'td:eq(2)' ).html( Parent.NickName );
		TreeLine.children( 'td:eq(2)' ).css( 'min-width', '68px' );
		TreeLine.children( 'td:eq(3)' ).html( Parent.content.length + '字' );
		TreeLine.children( 'td:eq(4)' ).children( 'span' ).html( this.ShowTime( Parent.CreateTime ));
		tbody.append( TreeLine );
		_( Parent.Children || [] ).chain().reverse().each( function( childId )
		{
			frm.DrawTreeLine( rootId, childId, tbody, layer + 1 );
		} );
	};

	this.ReplyOK = function( replyData )
	{
		console.log( replyData );
		var ParentId = 'Atcl_' + replyData[1].ParentID;
		var Parent = $( '#' + ParentId );
		var NewAtcl = this.ShowSingleAtcl( replyData );
		$( '.atcltop>.lineright>span', NewAtcl ).click( SetView );
		$( '.reply', NewAtcl ).click( EnableReply );
		QueryPop( $( '.atclleft .query', NewAtcl ), 'userpubk' );
		NewAtcl.hide();
		Parent.after( NewAtcl );
		NewAtcl.show( 400 );
		$( '.input', Parent ).hide( 300 );
	}

	this.RandomArt = function( data )
	{
		var Bound = [
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					];

		var x = 8;
		var y = 4;

		Bound[y][x] = -1;

		_( data ).each( function( c )
		{
			var Byte = c.charCodeAt();
			for( var i = 0; i < 4; i++ )
			{
				if( Byte & 0x01 && x < 16 )
				{
					x++;
				}
				else if( !( Byte & 0x01 ) && x > 0 )
				{
					x--;
				}

				if( Byte & 0x02 && y < 8 )
				{
					y++;
				}
				else if( !( Byte & 0x02 ) && y > 0 )
				{
					y--;
				}

				if( Bound[y][x] >= 0 )
				{
					Bound[y][x]++;
				}
				
				Byte >>= 2;
			}
		} );

		Bound[y][x] = -2;

		var s = '';
		_( Bound ).each( function( ln )
		{
			_( ln ).each( function( n )
			{
				s += n >= 0 ? ' .o+=*BOX@%&#/^QMZ'[n] : 'ES'[n + 2];
			} );
			s += '<br/>'
		} );

		return s.replace( / /g, '&nbsp;' );
	};

	this.GetNextPage = function()
	{
		var Param = {
			'cmd': 'GetTpcList',
			'start': this.StartPos,
			'label': this.ListLabel,
			'sortby': this.SortCol,
					};
		//console.log( Param );

		if( this.StartPos == 0 )
		{
			$( '#tpclist>table>tbody>tr:gt(0)' ).remove();
		}

		frm.Owner.Post( Param, 'GetResult' );
	};

	this.FillZero = function( s )
	{
		return ( '00' + s ).slice( -2 );
	};

	this.ShowTime = function( intTime, onlyDate )
	{
		var d = new Date();
		d.setTime( intTime );
		if( onlyDate )
		{
			return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate());
		}
		return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate()) + ' '
				+ this.FillZero( d.getHours()) + ':' + this.FillZero( d.getMinutes()) + ':' + this.FillZero( d.getSeconds());
	};

	this.ResetNewTpcInput = function()
	{
		$( '#tpcinput' ).hide( 300, function()
		{
			$( '#tpcinput td' ).remove();
		} );
	};

	this.TopicTR = function( tpcdata )
	{
		var TR = $( '<tr class="new" id="Topic_' + tpcdata[0] + '"><td class="title"></td> \
			<td class="first"></td><td class="num">1</td><td class="last"></td></tr>' );
		var LabelSpans = _( tpcdata[2].replace( /\|/g, ',' ).split( ',' )).chain().map( function( lb )
			{
				return '<span class="tpclabel">' + lb + '</span>';
			} ).value().join( '' );
		//console.log( LabelSpans );
		var Title = '<span class="arrow" title="升维">◣</span><span class="title" title="进入话题">' + tpcdata[1] + '</span>' + LabelSpans;
		TR.children( 'td:eq(0)' ).html( Title )
		TR.children( 'td:eq(1)' ).html( tpcdata[5] + '<br><span class="firsttime">' + this.ShowTime( tpcdata[6], true ) + '</span>' );
		TR.children( 'td:eq(2)' ).html( tpcdata[4] )
		TR.children( 'td:eq(3)' ).html( '<span class="lasttime" title="查看更新">' + this.ShowTime( tpcdata[8] ) + '</span><br>' + tpcdata[7] );
		TR.data( 'root', tpcdata[0] );

		return TR;
	};

	this.Init();
}